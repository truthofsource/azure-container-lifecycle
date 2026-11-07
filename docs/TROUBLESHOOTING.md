# Troubleshooting the lifecycle

| Symptom | Investigate | Do not assume |
| --- | --- | --- |
| Docker command exists but build fails to connect | CLI path, selected Docker context and Linux engine reachability. | That Docker is not installed. |
| Build stalls during package updates | Base-image downloads, package mirror response and build-cache use. | That increasing every CI timeout fixes the dependency. |
| Browser executable is missing | Match the Playwright package and base-image version, platform and runtime user. | That installing a different browser locally repairs the image. |
| Build passed but runtime smoke did not run | Selected target and final verification-stage output. | That building the earlier runtime stage exercised all checks. |
| Image pull fails | Registry name, digest existence, pull identity, registry permission and network path. | That a managed identity automatically grants registry access. |
| Wrong version appears | Job image binding, selected registry manifest and actual execution image. | That a tag still points to yesterday's bytes. |
| Job is configured but no report arrives | Trigger, enable switches, work lease, provider sign-in, export result and database outcome. | That deploying an image starts useful work. |
| A response was lost | Pending journal and saved payload, then the corresponding server result. | That a fresh download and blind retry are safe. |
| Image selection is rejected | Consumer identity, current image, active runs, release evidence and changed settings. | That bypassing a check is an image-only correction. |

The initial Terraform example had compact block-formatting errors; these were corrected before validation. That was an example-file issue, not an Azure service failure. Current results and outstanding engine-dependent checks are in [validation](VALIDATION.md).
