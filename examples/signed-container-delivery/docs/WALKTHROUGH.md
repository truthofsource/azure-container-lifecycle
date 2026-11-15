# Implementation walkthrough

**Terms used here:** A digest is a file or container fingerprint used to confirm the exact version. An artifact is a file produced for a release, such as an application ZIP or container image.

An operational application had several deployment targets and security scanners. A green build alone did not establish which source, package and container digest would reach production or what could be restored after a bad release.

## 1. Build the package

Run the local demo to create deterministic test-only ZIPs. Fixed timestamps and sorted entries allow identical inputs to produce identical bytes.

## 2. Exercise the policy gate

The gate binds a receipt to source and SHA-256. Modified bytes, out-of-date evidence, partial scans and blocking dependency findings fail before the local pointer changes.

## 3. Promote and recover

The same package is copied into content-addressed storage. Rollback re-verifies the prior package and changes a small atomic pointer; it does not rebuild the old branch.

## 4. Connect the scanner roles

Trivy covers dependencies, images and misconfiguration; Checkov covers IaC policies; TruffleHog looks for secrets; passive authenticated ZAP observes allowed HTTP paths. These tools answer different questions. Signing and provenance require separate identity and verification controls.

## Read the implementation

Start with [the domain module](../lab/domain.py), then [its tests](../tests/test_domain.py). The [dashboard report](../lab/demo.py) runs the same implementation; it does not substitute static success labels. `python -B -m lab demo` exits with an error if a demonstration assertion fails.

## Discuss the result

Describe the business problem first, the trust boundary second and the observed result third. Claim only the evidence in the validation record. A portable reference test is useful evidence of code behavior; it is not live-provider acceptance.

## Commands for this walkthrough

Start from the repository root. Run the working artifact promotion and rollback reference and its tests:

```bash
python -B -m unittest discover -s tests -v
python -B -m lab demo
```

Then follow the commands beside each [proof section](../README.md#proof-it-works). The [full command reference](COMMANDS.md) explains prerequisites, expected outcomes and which additional procedures have not been run.

## Follow the actual implementation

Read [the implemented path](IMPLEMENTATION.md), then [the selected source](../reference/) and original tests. The loopback workbench remains a portable local reference. It does not replay provider operations or prove a fresh hosted deployment.
