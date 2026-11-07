import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm, access, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createJournal } from '../src/journal.mjs';
import { digest } from '../src/import-cycle.mjs';

test('exclusive journal lock prevents overlapping job executions', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'carebridge-journal-'));
  try {
    const first = await createJournal(directory), second = await createJournal(directory);
    const release = await first.lock();
    await assert.rejects(second.lock(), /runner_locked/);
    await release(); await (await second.lock())();
  } finally { await rm(directory, { recursive: true }); }
});
test('retains pending payload across reopening and removes it only after completion', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'carebridge-journal-'));
  try {
    const csv = 'HEADER\nsynthetic\n', sourceHash = digest(csv);
    const first = await createJournal(directory);
    await first.prepare('clients', { status: 'commit_pending', sourceHash }, csv);
    const reopened = await createJournal(directory);
    assert.equal((await reopened.read('clients')).status, 'commit_pending');
    assert.equal(await reopened.payload('clients', sourceHash), csv);
    await assert.rejects(reopened.payload('clients', 'wrong'), /pending_payload_mismatch/);
    await reopened.complete('clients', { status: 'committed', sourceHash });
    assert.equal((await first.read('clients')).status, 'committed');
    await assert.rejects(access(join(directory, 'clients.pending.csv')));
    const archived = join(directory, 'archive', `clients-${sourceHash}`);
    assert.equal(await readFile(archived + '.csv', 'utf8'), csv);
    await reopened.prepare('visits', { status: 'commit_pending', sourceHash }, csv);
    const completed = Date.parse(JSON.parse(await readFile(archived + ".json", "utf8")).completedAtUtc);
    await reopened.prune(completed + 3 * 24 * 60 * 60_000 - 1);
    await access(archived + '.csv');
    await reopened.prune(completed + 3 * 24 * 60 * 60_000);
    await assert.rejects(access(archived + '.csv'));
    await access(archived + '.json');
    assert.equal(await reopened.payload('visits', sourceHash), csv);
    await assert.rejects(first.read('../outside'), /journal_unreadable/);
  } finally { await rm(directory, { recursive: true }); }
});

test('unchanged checks advance freshness without overwriting last imported time', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'carebridge-journal-'));
  try {
    const journal = await createJournal(directory);
    await journal.checked('clients', { status: 'committed' });
    const imported = (await journal.checks()).clients.lastImportedAtUtc;
    await journal.checked('clients', { status: 'unchanged' });
    const check = (await journal.checks()).clients;
    assert.equal(check.lastImportedAtUtc, imported);
    assert.equal(check.status, 'unchanged');
    assert.ok(check.lastCheckedAtUtc);
  } finally { await rm(directory, { recursive: true }); }
});

test('failed preview exports survive successful-file retention without advancing import state', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'carebridge-journal-'));
  try {
    const journal = await createJournal(directory), csv = 'HEADER\nsynthetic\n';
    await journal.failed('visits', csv, 'preview_contract_mismatch');
    await journal.prune(Date.now() + 100 * 24 * 60 * 60_000);
    assert.equal(await readFile(join(directory, 'failed', `visits-${digest(csv)}.csv`), 'utf8'), csv);
    assert.equal(await journal.read('visits'), undefined);
    assert.deepEqual(await journal.checks(), {});
  } finally { await rm(directory, { recursive: true }); }
});
