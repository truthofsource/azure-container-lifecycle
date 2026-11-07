// Emit only fixed stage names and elapsed time; never source records or errors.
export function startTiming(report, emit = event => console.log(JSON.stringify(event)), now = () => performance.now()) {
  let previous = now();
  return stage => {
    const current = now();
    try { emit({ event: 'carebridge_timing', report, stage, elapsedMs: Math.max(0, Math.round(current - previous)) }); }
    catch { /* Diagnostics must not interrupt an import. */ }
    previous = current;
  };
}
