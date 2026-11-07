# Pipelines, registry storage and deployment

## What the real source shows

The importer CI job installs recorded Node dependencies, runs worker tests, uses a local storage emulator for separate integration coverage, builds the Dockerfile and runs an offline synthetic browser check. This project copies selected original unit tests, not the full private CI dependency set.

The reviewed image-signing source pulls an exact registry digest, performs an isolated runtime check, scans those exact image bytes and creates software inventories. It signs release-selection evidence with a dedicated key. This does not establish the original builder's identity or complete build provenance merely because the statement contains an accepting source revision.

The selection workflow verifies its registered consumer, image and signing evidence before changing a job's image. Its pure checks are included here; its Azure adapter, signing key, real policy and live execution path are not. Source controls are not a claim that every historical image was accepted through them.

## Related infrastructure and ownership

The deployed CareBridge job is ARM-defined. The fictionalized [ARM reference](../reference/arm/private-worker.json) preserves the structure: digest-selected image, separate user-assigned identity, registry authentication, one CPU, 2 GiB memory, zero automatic retries, 840-second timeout and separate enable/schedule settings.

The new [Terraform root](../infra/main.tf) is a teaching equivalent for a **manual fictional demo job**, default Off. It assumes a separately created Container Apps environment, registry and pull identity. It creates none of those dependencies and grants no role, secret access or network path. Never import the production ARM-owned job into this example's state as a documentation exercise.

The [network module](../reference/terraform/network/) is related selected implementation source, kept as a reference rather than connected to the teaching root. A managed identity grants authentication, not automatic network reachability.

## Four separate decisions

1. Build an image and verify its local behavior.
2. Publish it to a registry and record the selected registry digest.
3. Change the intended job's image while preserving its other settings.
4. Start or schedule an execution under the application's separate enable and work-ownership checks.

An image change does not itself start the job. A job start does not prove the provider accepted sign-in or that the database committed a report.

## Public GitHub workflow

The manual-only workflow runs local tests and fictional demonstrations. A separate default-false input permits a Linux image build when explicitly requested. It has no Azure login, registry publisher credential, provider account or deployment step.

Reference: [Azure Container Apps Jobs](https://learn.microsoft.com/en-us/azure/container-apps/jobs), [Terraform job resource](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/container_app_job).
