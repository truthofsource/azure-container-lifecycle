# Release Engineering from the Operational Platform

**Terms used here:** A digest is a file or container fingerprint used to confirm the exact version. An artifact is a file produced for a release, such as an application ZIP or container image.

The production publisher promotes archived API/web packages selected by exact source and SHA-256. Rollback prepares an expiring candidate with current/target references, a contract ledger and settings/identity/storage fingerprints. Preparation itself cannot authorize production. A single publisher deployment lock serializes normal release and rollback; cancellation stays disabled.

The October 29 commissioning record describes a nonproduction prior-pair rehearsal and forward restoration, temporary runner cleanup and preserved paused services. It explicitly does not describe a production rollback, data restore, worker-image rollback or paid business transaction. This portfolio refresh performs none of those actions.

The included checks keep the historical schema-168 rules used by that test. They are not the current database schema or a rule for every future rollback. A real incident needs the current reviewed release record and compatible packages. The GitHub plan did not support the built-in required-reviewer feature, so the implemented approval checks the exact account and release candidate. The unused built-in-reviewer helper is left out.

Images are digest-pinned in the real delivery process. Registry/OIDC scope, scanner findings, signature/provenance checks and runtime health are separate evidence. This repository does not claim every remaining vulnerability was fixed or that the public fixture's policy receipt is trusted scanner evidence.

## Actual source and adaptations

Read [the source map](SOURCE-MAP.md) and [machine provenance](source-map.json) for every extracted implementation file.

## Dedicated recovery case study

The [backup and recovery project](https://github.com/truthofsource/azure-backup-and-recovery) goes deeper into key-version coverage, backup receipts, isolated recovery and data/file/state dependencies. Application artifact rollback and data recovery solve different problems.
