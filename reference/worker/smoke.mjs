// Synthetic container acceptance only: never opens either business portal.
import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve, dirname, basename } from 'node:path';
import { chromium } from 'playwright';
import { createJournal } from './journal.mjs';
import { digest } from './import-cycle.mjs';
import {runMfaBrowserAcceptance} from './mfa-smoke.mjs';

const directory = await mkdtemp(join(tmpdir(), 'carebridge-smoke-'));
let browser;
try {
  assert.notEqual(process.getuid?.(), 0, 'Container must run as an unprivileged user');
  assert.notEqual(process.env.CAREBRIDGE_WORKER_ENABLED, 'true', 'Smoke job must keep imports disabled');
  browser = await chromium.launch({ headless: true });
  await runMfaBrowserAcceptance(browser);
  const page = await browser.newPage();
  await page.setContent('<title>CareBridge synthetic acceptance</title><button>Ready</button>');
  assert.equal(await page.getByRole('button').textContent(), 'Ready');
  const journal = await createJournal(directory), release = await journal.lock();
  try {
    const csv = 'Header\nSynthetic\n', sourceHash = digest(csv);
    await journal.prepare('clients', { status: 'commit_pending', sourceHash }, csv);
    assert.equal(await journal.payload('clients', sourceHash), csv);
    await journal.complete('clients', { status: 'committed', sourceHash, rows: 1, batchId: 'synthetic' });
    assert.equal((await journal.read('clients')).status, 'committed');
  } finally { await release(); }
  console.log(JSON.stringify({ status: 'passed', browser: 'chromium', unprivileged: true,
    syntheticJournal: true, businessRequests: 0, durableStorageVerified: false }));
} finally {
  if (browser) await browser.close();
  assert.equal(dirname(resolve(directory)), resolve(tmpdir()));
  assert.ok(basename(directory).startsWith('carebridge-smoke-'));
  await rm(directory, { recursive: true, force: true });
}
