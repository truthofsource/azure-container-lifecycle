import { mkdir, readFile, writeFile, rename, open, unlink, readdir } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { digest, reportOrder, ImportFailure } from './import-cycle.mjs';

export async function createJournal(directory) {
  const root = resolve(directory);
  await mkdir(root, { recursive: true, mode: 0o700 });
  function path(type, suffix) {
    if (!reportOrder.includes(type)) throw new ImportFailure('unknown_report_type');
    return join(root, type + suffix);
  }
  async function atomic(file, data) {
    const temporary = file + '.' + randomUUID() + '.tmp';
    await writeFile(temporary, data, { mode: 0o600, flag: 'wx' });
    await rename(temporary, file);
  }
  return {
    async lock() {
      let handle;
      try { handle = await open(join(root, 'runner.lock'), 'wx', 0o600); }
      catch { throw new ImportFailure('runner_locked'); }
      await handle.writeFile(JSON.stringify({ pid: process.pid, startedAtUtc: new Date().toISOString() }));
      return async () => { await handle.close(); await unlink(join(root, 'runner.lock')); };
    },
    async readIdentities(scope) {
      try { const value=JSON.parse(await readFile(join(root,'identities.json'),'utf8')); return value.scope===scope ? value.entries : {}; }
      catch(error) { if(error.code==='ENOENT') return {}; throw new ImportFailure('identity_cache_invalid'); }
    },
    async saveIdentities(scope, entries) { await atomic(join(root,'identities.json'),JSON.stringify({scope,entries})); },
    async read(type) {
      try { return JSON.parse(await readFile(path(type, '.json'), 'utf8')); }
      catch (error) { if (error.code === 'ENOENT') return undefined; throw new ImportFailure('journal_unreadable'); }
    },
    async prepare(type, receipt, csv) {
      await atomic(path(type, '.pending.csv'), csv);
      await atomic(path(type, '.json'), JSON.stringify(receipt));
    },
    async payload(type, sourceHash) {
      const csv = await readFile(path(type, '.pending.csv'), 'utf8');
      if (digest(csv) !== sourceHash) throw new ImportFailure('pending_payload_mismatch');
      return csv;
    },
    async complete(type, receipt) {
      const csv = await readFile(path(type, '.pending.csv'), 'utf8');
      if (digest(csv) !== receipt.sourceHash) throw new ImportFailure('pending_payload_mismatch');
      const archive = join(root, 'archive');
      await mkdir(archive, { recursive: true, mode: 0o700 });
      const base = join(archive, `${type}-${receipt.sourceHash}`);
      await atomic(base + '.csv', csv);
      await atomic(base + '.json', JSON.stringify({ ...receipt, completedAtUtc: new Date().toISOString() }));
      await atomic(path(type, '.json'), JSON.stringify(receipt));
      await unlink(path(type, '.pending.csv')).catch(error => { if (error.code !== 'ENOENT') throw error; });
    },
    async failed(type, csv, code) {
      path(type, '.json'); // Validate the report before constructing an archive path.
      const failed = join(root, 'failed');
      await mkdir(failed, { recursive: true, mode: 0o700 });
      const base = join(failed, `${type}-${digest(csv)}`);
      await atomic(base + '.csv', csv);
      await atomic(base + '.json', JSON.stringify({ type, sourceHash: digest(csv), code,
        failedAtUtc: new Date().toISOString(), status: 'needs_attention' }));
    },
    async checks() {
      try { return JSON.parse(await readFile(join(root, 'checks.json'), 'utf8')); }
      catch (error) { if (error.code === 'ENOENT') return {}; throw new ImportFailure('journal_unreadable'); }
    },
    async checked(type, result) {
      const checks = await this.checks();
      checks[type] = { ...checks[type], lastCheckedAtUtc: new Date().toISOString(), status: result.status,
        ...(result.status === 'committed' ? { lastImportedAtUtc: new Date().toISOString() } : {}) };
      await atomic(join(root, 'checks.json'), JSON.stringify(checks));
    },
    async prune(now = Date.now()) {
      const archive = join(root, 'archive');
      const files = await readdir(archive).catch(error => { if (error.code === 'ENOENT') return []; throw error; });
      for (const file of files) {
        if (!/^(clients|authorizations|appointments|visits|noncompliant)-[a-f0-9]{64}\.json$/.test(file)) continue;
        const receipt = JSON.parse(await readFile(join(archive, file), 'utf8'));
        const completed = Date.parse(receipt.completedAtUtc);
        if (receipt.status !== 'committed' || !Number.isFinite(completed) || now - completed < 3 * 24 * 60 * 60_000) continue;
        // Only confirmed archive CSVs expire. Keep receipts and pending files.
        await unlink(join(archive, file.replace(/\.json$/, '.csv'))).catch(error => { if (error.code !== 'ENOENT') throw error; });
      }
    },
    async status(value) { await atomic(join(root, 'last-run.json'), JSON.stringify(value, null, 2)); },
  };
}
