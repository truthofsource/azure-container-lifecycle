# From business requirement to useful container work

The lifecycle starts with a task and its source code, before the Dockerfile. The following stages explain the implementation and review sequence; they are not a claim that a fresh deployment was performed for this project.

## 1. Start with the job

Define the report-import task and the code that performs it. The Dockerfile packages that code; it is not the beginning of the business solution.

**Keep:** Source code and tests.

## 2. Record the dependencies

The package files record the software the worker needs. The lockfile preserves selected versions and download fingerprints.

**Keep:** package.json and package-lock.json.

## 3. Choose the build inputs

The Dockerfile describes the image and the build context supplies its files. The ignore file limits this context to package files and source.

**Keep:** Dockerfile and .dockerignore.

## 4. Build the image

Docker combines the pinned browser base, installed packages and worker code into an image. It sets the working folder, lower-permission user and default command.

**Keep:** Local image.

## 5. Verify the packaged runtime

The final verification stage runs a fictional browser check as the selected image user. This is a build check, not permission to sign into CareBridge.

**Keep:** Synthetic browser result.

## 6. Review software security

The platform checks selected software and exact image bytes with its security tooling. Findings and software inventories remain evidence for the release decision.

**Keep:** Trivy reports and software inventory.

## 7. Store it in the registry

Azure Container Registry stores the image for later use. A tag is a convenient name, while the registry digest identifies the selected manifest.

**Keep:** Registry image and digest.

## 8. Check release evidence

The reviewed signing path binds release-selection evidence to the selected image and accepting source. It does not by itself prove which original build produced that image.

**Keep:** Signed release-selection evidence.

## 9. Select the deployment image

The deployment process changes the registered job to the intended image digest. It checks existing settings and identity so an image update does not silently activate other behavior.

**Keep:** Job configuration.

## 10. Activate work separately

A job execution creates a running container from the selected image. Scheduling, enable switches and the application work lease separately control whether real report work is allowed.

**Keep:** Execution and work request.

## 11. Observe useful outcomes

Logs and saved records show whether a run started, checked unchanged data or committed an import. A started container alone does not establish that a business report was imported.

**Keep:** Execution logs and import records.

## 12. Keep a recovery path

Retain the required previous image and reconcile unfinished work before a rollback. Replacing an image does not restore a provider session, database or saved report state.

**Keep:** Previous digest and recovery record.

## Terms that are easy to confuse

| Term | Plain meaning |
| --- | --- |
| Source | The program and setup files under review. |
| Dockerfile | Instructions for building an image. |
| Build context | The files available to the builder, limited by the ignore file. |
| Image | Packaged software and its startup settings. |
| Container | A running instance of an image. |
| Tag | A name that can be moved to another image. |
| Registry digest | The fingerprint used to select a registry manifest. |
| Job | Azure configuration describing how an execution should run. |
| Execution | One run of that job. |
| Import outcome | The application result, such as unchanged data or a committed report. |

The directory worker is a different deployment pattern: Azure Functions ZIP packaging. It is not presented as the Docker example here.
