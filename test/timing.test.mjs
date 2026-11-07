import test from 'node:test';
import assert from 'node:assert/strict';
import { startTiming } from '../src/timing.mjs';

test('diagnostics cannot fail an import and use elapsed monotonic stage time', () => {
  let clock = 100;
  const events = [];
  const mark = startTiming('appointments', event => { events.push(event); if (events.length === 1) throw new Error('sink unavailable'); }, () => clock);
  clock = 125; assert.doesNotThrow(() => mark('read_assignments'));
  clock = 160; mark('verify_caregiver_ids');
  assert.deepEqual(events, [
    { event: 'carebridge_timing', report: 'appointments', stage: 'read_assignments', elapsedMs: 25 },
    { event: 'carebridge_timing', report: 'appointments', stage: 'verify_caregiver_ids', elapsedMs: 35 },
  ]);
});
