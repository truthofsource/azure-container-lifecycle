# Operation, growth and recovery

The deployed worker uses a private report-processing path and saved sign-in/state. The public example uses temporary local files and simulated submission; that does not establish real Blob durability, provider access or a live database commit.

## Useful observations

Track image digest, execution start/end, safe failure category, browser startup time, export waits and report-specific import outcome. Do not put credentials, email codes, source CSV contents or employee details into release reports. The actual timing helper emits fixed stage labels and elapsed time.

Distinguish a new imported file from an unchanged check. The original journal tests confirm that a successful unchanged check can advance its check time without rewriting the last import time.

## Growth and costs

Measure CPU, memory, browser startup, export duration, queue delays and provider limits before increasing concurrency. More containers do not automatically create more safe provider sessions; saved sign-in and application work leases remain shared concerns.

Browser images are large, and operating-system package upgrades can dominate build time. Reuse unchanged build layers where suitable and avoid repeating passing CI jobs just to retry a failed download. Cached layers still need a deliberate security-refresh policy.

Container job CPU/memory runtime, registry storage, retained old images, state storage, networking and logs have separate costs. A job with no current execution can still depend on retained paid infrastructure.

## Recovery

Reconcile pending import work before replaying a submission or choosing an older image. Retain the exact saved payload when a commit response is uncertain. Image rollback does not undo database changes or make an expired provider session valid.

Keep previous images only while needed by an active binding, accepted rollback path or recovery record. Do not purge an image solely because its tag looks old.

## Strengths and limits

The package makes the browser and program explicit, but does not remove provider layout changes or multi-factor sign-in. Digest selection improves release identification, but does not prove every security property or the original build process. Default-Off examples reduce accidental activation, but do not replace a real environment's permissions and connectivity checks.
