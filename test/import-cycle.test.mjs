import { test } from 'node:test';
import assert from 'node:assert/strict';
import { digest, importReport, runCycle, ImportFailure } from '../src/import-cycle.mjs';

const csv = 'HEADER\nsynthetic\n';
const batchId = '12345678-1234-1234-1234-123456789abc';
function fixture() {
  const records = new Map(), payloads = new Map(), calls = [];
  const journal = {
    async read(type) { return records.get(type); },
    async prepare(type, receipt, bytes) { calls.push('prepare'); records.set(type, receipt); payloads.set(type, bytes); },
    async complete(type, receipt) { calls.push('complete'); records.set(type, receipt); },
    async payload(type) { return payloads.get(type); },
  };
  const adapter = {
    async preview(type, bytes) { calls.push(['preview', type, bytes]); return { importType: type, sourceFileSha256: digest(bytes), rowCount: 1, reconciliation: { resolved: 0, pendingClientIntake: 1, conflict: 0, needsReview: 0 } }; },
    async commit(type, bytes) { calls.push(['commit', type, bytes]); return { batchId, status: 'completed', rowCount: 1, idempotentReplay: false }; },
  };
  return { journal, adapter, calls, records, payloads };
}
test('default preview never submits or journals a commit', async () => {
  const f = fixture(); const r = await importReport({ type: 'clients', csv, ...f });
  assert.equal(r.status, 'previewed'); assert.equal(f.calls.length, 1);
});
test('persists intent before sending the exact previewed bytes; skips an unchanged committed file', async () => {
  const f = fixture(); await importReport({ type: 'clients', csv, ...f, commit: true });
  assert.deepEqual(f.calls.map(c => Array.isArray(c) ? c[0] : c), ['preview', 'prepare', 'commit', 'complete']);
  assert.equal(f.calls[0][2], f.calls[2][2]);
  assert.equal((await importReport({ type: 'clients', csv, ...f, commit: true })).status, 'unchanged');
  assert.equal(f.calls.length, 4);
});
test('rejects preview hash changes and nested reconciliation conflicts', async () => {
  for (const patch of [{ sourceFileSha256: 'wrong' }, { visits: { employee: { conflict: 1 } } }]) {
    const f = fixture(), original = f.adapter.preview;
    f.adapter.preview = async (...args) => ({ ...await original(...args), ...patch });
    await assert.rejects(importReport({ type: 'clients', csv, ...f, commit: true }));
    assert.equal(f.calls.length, 1);
  }
});
test('a lost response retains pending bytes and does not retry in the same call', async () => {
  const f = fixture(); f.adapter.commit = async () => { f.calls.push('lost-response'); throw Error('connection'); };
  await assert.rejects(importReport({ type: 'clients', csv, ...f, commit: true }));
  assert.equal(f.records.get('clients').status, 'commit_pending');
  assert.equal(f.payloads.get('clients'), csv);
  assert.equal(f.calls.filter(c => c === 'lost-response').length, 1);
  await assert.rejects(importReport({ type: 'clients', csv: csv + 'new\n', ...f, commit: true }), /resolve_previous_commit_first/);
});
test('recovery uses the saved payload before downloading newer data', async () => {
  const f = fixture(); await f.journal.prepare('clients', { status: 'commit_pending', sourceHash: digest(csv) }, csv);
  let downloaded = false; f.adapter.commit = async () => ({ batchId, status: 'completed', rowCount: 1, idempotentReplay: true });
  const results = await runCycle({ types: ['clients'], source: { async download() { downloaded = true; } }, ...f, commit: true });
  assert.equal(downloaded, false); assert.equal(results[0].idempotentReplay, true);
});

test('SQL replay UUID casing cannot change the durable batch identity', async () => {
  const f = fixture();
  f.adapter.commit = async () => ({ batchId: batchId.toUpperCase(), status: 'completed', rowCount: 1, idempotentReplay: true });
  const result = await importReport({ type: 'clients', csv, ...f, commit: true });
  assert.equal(result.status, 'unchanged');
  assert.equal(result.batchId, batchId);
  assert.equal(f.records.get('clients').batchId, batchId);
});
test('runs predecessors first and stops after a failed import', async () => {
  const f = fixture(); const downloaded = [];
  const source = { async download(type) { downloaded.push(type); if (type === 'authorizations') throw Error('source failed'); return csv; } };
  await assert.rejects(runCycle({ types: ['visits', 'authorizations', 'clients'], source, ...f, commit: true }));
  assert.deepEqual(downloaded, ['clients', 'authorizations']);
});
test('rejects partial completion without marking the source imported', async () => {
  const f = fixture(); f.adapter.commit = async () => ({ batchId, status: 'completed_with_errors', rowCount: 1 });
  await assert.rejects(importReport({ type: 'clients', csv, ...f, commit: true }), /commit_requires_review/);
  assert.equal(f.records.get('clients').status, 'commit_pending');
});

test('records report failures and continues independent reports without logging error details', async () => {
  const f = fixture(), failed = [], checked = [];
  f.journal.failed = async (...args) => failed.push(args);
  f.journal.checked = async type => checked.push(type);
  const original = f.adapter.preview;
  f.adapter.preview = async (type, bytes) => {
    if (type === 'visits') throw Error('private server response');
    return original(type, bytes);
  };
  const results = await runCycle({ types: ['visits', 'noncompliant'], source: { async download() { return csv; } }, ...f, commit: true, continueOnError: true });
  assert.deepEqual(results.map(r => r.status), ['needs_attention', 'committed']);
  assert.deepEqual(checked, ['noncompliant']);
  assert.deepEqual(failed, [['visits', csv, 'automation_failed']]);
  assert.equal(JSON.stringify(results).includes('private server response'), false);
});

test('expired shared login stops remaining reports and labels them skipped', async () => {
  const f = fixture(), downloads = [];
  const results = await runCycle({ types: ['visits', 'noncompliant'], source: { async download(type) {
    downloads.push(type); throw new ImportFailure('sign_in_required');
  } }, ...f, continueOnError: true });
  assert.deepEqual(downloads, ['visits']);
  assert.deepEqual(results.map(r => r.status), ['needs_attention', 'skipped']);
});

test('established worker prioritizes Appointments ahead of due daily references', async () => {
  const f = fixture(), downloaded = [];
  for (const type of ['clients', 'authorizations']) f.records.set(type, { status: 'committed', rows: 1, batchId, sourceHash: digest(csv) });
  const results = await runCycle({ types: ['clients', 'authorizations', 'appointments', 'visits'], prioritizeAppointments: true,
    source: { async download(type) { downloaded.push(type); return csv; } }, ...f, commit: true });
  assert.deepEqual(downloaded, ['appointments', 'clients', 'authorizations', 'visits']);
  assert.equal(results[0].type, 'appointments');
});

test('bootstrap and pending prerequisite recovery retain reference-first order', async () => {
  for (const pending of [false, true]) {
    const f = fixture(), downloaded = [];
    if (pending) await f.journal.prepare('clients', { status: 'commit_pending', sourceHash: digest(csv) }, csv);
    const results = await runCycle({ types: ['appointments', 'clients', 'authorizations'], prioritizeAppointments: true,
      source: { async download(type) { downloaded.push(type); return csv; } }, ...f, commit: true });
    assert.deepEqual(results.map(x => x.type), ['clients', 'authorizations', 'appointments']);
    assert.deepEqual(downloaded, pending ? ['authorizations', 'appointments'] : ['clients', 'authorizations', 'appointments']);
  }
});

test('prioritized Appointments still replay only the saved payload after uncertain commit', async () => {
  const f = fixture(), downloaded = [];
  for (const type of ['clients', 'authorizations']) f.records.set(type, { status: 'committed', rows: 1, batchId, sourceHash: digest(csv) });
  await f.journal.prepare('appointments', { status: 'commit_pending', sourceHash: digest(csv) }, csv);
  f.adapter.commit = async () => { throw new ImportFailure('commit_requires_review'); };
  const results = await runCycle({ types: ['clients', 'appointments'], prioritizeAppointments: true, continueOnError: true,
    source: { async download(type) { downloaded.push(type); return csv; } }, ...f, commit: true });
  assert.deepEqual(downloaded, ['clients']); assert.equal(results[0].code, 'commit_requires_review');
  assert.equal(f.records.get('appointments').status, 'commit_pending');
});
