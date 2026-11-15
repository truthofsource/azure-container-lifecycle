# Troubleshooting lessons from the actual platform

These are historical engineering incidents summarized from maintained internal records. They are not newly reproduced tests, a fresh cloud inventory or instructions to repeat a consumed operation. Names, resource identifiers, private payloads and credentials are excluded.

## Another runner did not solve exhausted artifact storage

**What happened.** CI encountered account-capacity restrictions, and a later readiness job could not upload its artifacts. Running tests on another machine did not remove the artifact-storage blocker.

**What the evidence showed.** The failed upload explicitly reported artifact-storage quota. Hosted compute availability was a separate constraint; the inventory also showed that deleting only small readiness reports would barely change storage use.

**What changed and how it was checked.** Owner-authorized cleanup froze a retention plan, protected current and recovery dependencies, backed up available artifact ZIPs and checked their integrity before deleting selected older GitHub copies. Journals supported safe resumption after a transport failure. Hosted compute still needed separate recovery before the accepted retry.

**What to carry forward.** Treat compute minutes, artifact storage and retained recovery evidence as separate controls. Keep the latest usable packages and their receipts, not simply an arbitrary last few files; a self-hosted runner does not remove GitHub artifact limits.

Source record: `docs/troubleshooting/rollback-commissioning.md — GitHub compute and artifact storage are separate limits; October 28–29, 2026`. These internal paths identify provenance; they are not public file links.

## Runner registration arguments appeared in the VM journal

**What happened.** An early registration loop passed a short-lived runner registration token through sudo arguments, placing it in the VM journal.

**What the evidence showed.** Avoiding an explicit echo did not prevent process arguments from becoming retained operational output. The original trace therefore required private handling rather than publication in a troubleshooting example.

**What changed and how it was checked.** The recorded correction transferred registration material through stdin, refreshed it privately and allowed one job per registration. The operating guide also kept production credentials off the CI guest and required removal of the temporary runner resources after work finished. This summary does not assert a new credential revocation or runner test.

**What to carry forward.** Review process arguments and operating-system logs as well as application logging. A short lifetime reduces exposure duration but is not permission to retain or publish a token; stopping a temporary VM is also different from removing its billed resources.

Source record: `docs/troubleshooting/rollback-commissioning.md` — Runner registration diagnostics. The path identifies internal provenance, not a public file link.

## Evidence and project boundaries

The local examples and screenshots in this repository remain separate from the dated hosted incidents above. A new documentation summary does not establish another successful deployment, restore, security scan or business transaction. Follow the repository’s existing validation guide for the commands and limits of the runnable reference.

The practical sequence is: identify the failing boundary, preserve safe correlation evidence, reconcile any uncertain result, apply only the relevant repair and verify the resulting state. A completed local command is not interchangeable with a completed cloud operation.
