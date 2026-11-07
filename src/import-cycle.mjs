import { startTiming } from './timing.mjs';
import { createHash } from 'node:crypto';

export const reportOrder = ['clients', 'authorizations', 'appointments', 'visits', 'noncompliant', 'broadcasts'];
export class ImportFailure extends Error {
  constructor(code) { super(code); this.name = 'ImportFailure'; this.code = code; }
}
export function digest(csv) { return createHash('sha256').update(csv, 'utf8').digest('hex'); }

function validateCsv(csv) {
  if (typeof csv !== 'string' || Buffer.byteLength(csv, 'utf8') === 0 || Buffer.byteLength(csv, 'utf8') > 2 * 1024 * 1024) {
    throw new ImportFailure('invalid_csv_size');
  }
}
function needsReview(value) {
  if (!value || typeof value !== 'object') return false;
  return Object.entries(value).some(([key, count]) =>
    (['needsReview', 'conflict'].includes(key) && count !== 0) ||
    (typeof count === 'object' && needsReview(count)));
}

// Adapters own source authentication and storage. Neither CSV nor credentials are
// included in the returned status. Persist the exact payload before submitting it.
export async function importReport({ type, csv, adapter, journal, commit = false, sourceExportedAtUtc }) {
  if (!reportOrder.includes(type)) throw new ImportFailure('unknown_report_type');
  validateCsv(csv);
  const sourceHash = digest(csv);
  const prior = await journal.read(type);
  if (!adapter.alwaysCheckServer && prior?.status === 'committed' && prior.sourceHash === sourceHash) {
    return { type, status: 'unchanged', sourceHash, batchId: prior.batchId, rows: prior.rows };
  }
  if (prior?.status === 'commit_pending' && prior.sourceHash !== sourceHash) {
    throw new ImportFailure('resolve_previous_commit_first');
  }

  const timing = startTiming(type);
  const preview = await adapter.preview(type, csv, sourceExportedAtUtc);
  timing('api_preview');
  if (preview?.importType !== type || preview.sourceFileSha256 !== sourceHash ||
      !Number.isInteger(preview.rowCount) || preview.rowCount < 0 || preview.rowCount > 10_000 ||
      !preview.reconciliation || typeof preview.reconciliation !== 'object') {
    throw new ImportFailure('preview_contract_mismatch');
  }
  if (needsReview(preview.reconciliation) || needsReview(preview.appointments) || needsReview(preview.visits) || needsReview(preview.noncompliant)) {
    throw new ImportFailure('reconciliation_needs_review');
  }
  if (preview.rowCount === 0) return { type, status: 'empty', sourceHash, rows: 0 };
  if (!commit) return { type, status: 'previewed', sourceHash, rows: preview.rowCount };

  await journal.prepare(type, { status: 'commit_pending', sourceHash, rows: preview.rowCount,
    ...(sourceExportedAtUtc ? { sourceExportedAtUtc } : {}) }, csv);
  // Exactly one attempt here. After a lost response, recover the saved payload
  // through the API's exact-file idempotency before accepting another export.
  const result = await adapter.commit(type, csv, sourceExportedAtUtc);
  timing('journal_prepare_and_api_commit');
  if (!result || !/^[0-9a-f-]{36}$/i.test(result.batchId ?? '') ||
      result.rowCount !== preview.rowCount || result.status !== 'completed') {
    throw new ImportFailure('commit_requires_review');
  }
  const receipt = { type, status: 'committed', sourceHash, rows: result.rowCount,
    // SQL returns UUIDs in uppercase on replay; initial randomUUID() responses
    // are lowercase. Persist one spelling so immutable receipts compare identity.
    batchId: result.batchId.toLowerCase(), idempotentReplay: result.idempotentReplay === true };
  await journal.complete(type, receipt);
  return result.idempotentReplay === true ? { ...receipt, status: 'unchanged' } : receipt;
}

export async function runCycle({ types, source, adapter, journal, commit = false, continueOnError = false, prioritizeAppointments = false }) {
  if (!Array.isArray(types) || types.length === 0 || types.some(t => !reportOrder.includes(t)) || new Set(types).size !== types.length) {
    throw new ImportFailure('invalid_report_selection');
  }
  let order = reportOrder.filter(t => types.includes(t));
  // An established installation can refresh Appointments before daily reference
  // refreshes. Bootstrap or unresolved prerequisite commits retain dependency
  // order. API reconciliation still decides whether each exact import is valid.
  if (prioritizeAppointments && types.includes('appointments') && types.some(t => ['clients', 'authorizations'].includes(t))) {
    const prerequisites = await Promise.all(['clients', 'authorizations'].map(type => journal.read(type)));
    const established = prerequisites.every(row => row?.status === 'committed' && Number.isInteger(row.rows) && row.rows > 0 &&
      /^[0-9a-f-]{36}$/i.test(row.batchId ?? '') && /^[0-9a-f]{64}$/i.test(row.sourceHash ?? ''));
    if (established) order = ['appointments', ...order.filter(type => type !== 'appointments')];
  }
  const results = [];
  for (const type of order) {
    let csv;
    try {
      const pending = await journal.read(type);
      const downloaded = pending?.status === 'commit_pending'
        ? { csv: await journal.payload(type, pending.sourceHash), sourceExportedAtUtc: pending.sourceExportedAtUtc }
        : await source.download(type);
      csv = typeof downloaded === 'string' ? downloaded : downloaded.csv;
      const sourceExportedAtUtc = typeof downloaded === 'string' ? undefined : downloaded.sourceExportedAtUtc;
      if (pending?.status === 'commit_pending' && digest(csv) !== pending.sourceHash) {
        throw new ImportFailure('pending_payload_mismatch');
      }
      const result = await importReport({ type, csv, adapter, journal, commit, sourceExportedAtUtc });
      if (pending?.status !== 'commit_pending' && sourceExportedAtUtc) {
        result.checkedAtUtc = new Date().toISOString();
        result.sourceExportedAtUtc = sourceExportedAtUtc;
      }
      if (commit && journal.checked && pending?.status !== 'commit_pending') await journal.checked(type, result);
      results.push(result);
    } catch (error) {
      const code = error instanceof ImportFailure ? error.code : 'automation_failed';
      if (typeof csv === 'string' && journal.failed) await journal.failed(type, csv, code);
      if (!continueOnError) throw error;
      results.push({ type, status: 'needs_attention', code });
      // Expired authentication affects the shared connection. Avoid repeatedly
      // attempting login or proceeding with an unreadable durable journal.
      if (['sign_in_required', 'journal_unreadable', 'pending_payload_mismatch'].includes(code)) {
        for (const remaining of order.filter(t => !results.some(r => r.type === t))) {
          results.push({ type: remaining, status: 'skipped', code });
        }
        break;
      }
    }
  }
  return results;
}
