> This example is maintained within **azure-container-lifecycle**. Run its local commands from this subfolder; its nested workflow files are retained examples and are not active repository workflows. See [the consolidation guide](https://github.com/truthofsource/azure-container-lifecycle/blob/main/docs/CONSOLIDATION.md).

# DevSecOps Delivery & Verified Rollback

**Release the tested files and keep a verified previous version ready if something goes wrong.**

[The problem](#the-business-problem) · [The solution](#the-solution) · [What was built](#what-was-built) · [Proof it works](#proof-it-works) · [Run it](#run-it-locally) · [Step by step](#step-by-step)

## The Business Problem

The platform supports onboarding, timesheets, employee documents and payroll-related work. A release that behaves differently from the version tested can disrupt those services even when the build itself succeeded. Rebuilding at the final deployment step makes it harder to establish exactly which files staff are using.

If a release causes trouble, an old source branch is insufficient as a recovery plan: the team also needs the previous built files, matching evidence and a compatibility check against current settings and data. Security reports for a different version do not establish whether the selected release is acceptable.

The business need was a traceable release path and a prepared return path, with the tested package preserved through promotion and a verified earlier package available for a deliberate rollback.

## The Solution

Build once, keep the tested package and its fingerprint, and check the matching security results before release. Save a verified previous package for rollback, which means returning to an earlier release. Keep permission to publish packages separate from the application’s own access.

**Business outcome:** Make releases traceable and recovery deliberate, with fewer differences between the tested package and the released one.

### Platform implementation

- Built API/web saved release packages, exact-hash readiness checks and paired promotion so production used the verified packages instead of a new build.
- Added release and rollback checks for exact selected source, retained artifacts, settings preservation and cleanup of temporary release infrastructure.
- Integrated dependency, container, IaC and secret scanning with dated findings, package inventories and remediation evidence; separated report generation from release authorization.
- Patched vulnerable dependencies using compatible versions and tests that existing callers still work, retaining unresolved findings rather than claiming a clean estate.

This case study draws on a workforce/operations platform I designed and implemented. Organization details and records are excluded. The public code makes selected patterns reproducible; the local demonstration uses fictional data, and its placeholder screenshots have been removed. [Validation scope](docs/VALIDATION.md) separates that evidence from testing against the actual cloud service.

### Actual implementation code

This repository now includes selected implementation source and original tests from the operational platform, rather than only a portable reference. Read [what was implemented and accepted](docs/IMPLEMENTATION.md), [the source map](docs/SOURCE-MAP.md) and the dated validation boundaries. Identifying configuration is replaced with examples; original private history and records are excluded.

## Tools Used and What They Do

| Tool or service | What it does | Where it fits |
| --- | --- | --- |
| GitHub Actions | Coordinate selected-source checks, publication and reviewed recovery stages. | Actual platform process; public reference CI is manual-only. |
| GitHub CLI (gh) | Inspect exact workflow runs, retained artifacts and release metadata. | Operating utility; dispatch, publication and rollback remain separate actions. |
| Docker and Azure Container Registry | Build/package worker software and retain selected images. | Actual container boundaries; image publication is separate from execution. |
| Trivy, Checkov, TruffleHog and OWASP ZAP | Check dependencies/images, IaC, possible secrets and selected runtime access. | Separate scanner roles and evidence; the default local workflow does not run live scans. |
| SHA-256 and release manifests | Bind retained packages and receipts to exact selected content. | Integrity/evidence utilities, not proof of every runtime behavior. |
| Terraform and Azure CLI | Describe supporting access and inspect the intended target. | Scoped operating context, not automatic production rollback. |
| Python | Exercise the public release/rollback decision model. | Local reference; no Azure publisher credentials or deployment adapter. |

A retained ZIP, a successful build, a published package and a restored running release are different states. The public demonstration does not start an actual rollback.

## Step by Step

Your own built image, registry digest, signature verification and deployment/rollback to retained signed images.

[Open the standalone build guide](docs/BUILD-YOUR-OWN.md) or follow the same complete instructions below.

Start with a new folder, your own files and your own accounts. The numbered steps below describe the build; no portfolio repository checkout is required. The existing implementation/evidence elsewhere in this repository is a separate reference, not a claim that your new build has already passed.

### Prerequisites

Docker, Azure CLI, Cosign, your own ACR and a disposable local deployment host. Use harmless public-lab content; image signatures can publish digest/key metadata to a transparency log.

Use Bash on Linux/macOS/WSL for Bash blocks and PowerShell for PowerShell blocks. Select the tool versions supported by the official sources below, record the versions you actually install and retain generated dependency locks. Cloud resources, scanner downloads, logs and external AI calls can create costs; review the stated scope before enabling them.

### Create your project folder

Choose a new folder name. These first commands create a blank project; an optional `git init` gives it its own history. Create parent directories in your editor when a later step introduces a nested file.

```bash
mkdir my-secure-container-delivery-and-rollback
cd my-secure-container-delivery-and-rollback
git init
```

Create `.gitignore` before saving credentials or build outputs:

```gitignore
.venv/
node_modules/
.env
.env.*
local.settings.json
credentials.json
token.json
*.pem
*.key
*.tfstate*
*.tfplan
.terraform/
private*/
captures/
backups/
batch.json
reports/
out/
app-config.local.yaml
```

The source/file snippets are a starting implementation you type or paste into the named files. Replace `YOUR_*`, names, regions and addresses only with values from your own lab; do not place real client/employee records in a test project. Keep your terminal in this project root unless a step explicitly changes directory.

Before a first commit, set your own repository-local author with `git config user.name "YOUR_NAME"` and `git config user.email "YOUR_PUBLIC_COMMIT_EMAIL"`. Review `git status --short` and the staged diff before publishing; ignored local files are not a substitute for reviewing what you upload.

### Step 1 — Create a web image from your own files

**Where:** Your new project folder.

Create your site and Dockerfile below, replacing the entire FROM placeholder with the full reviewed RepoDigest reference printed by docker image inspect, for example nginx@sha256: followed by its hash. Do not paste that full reference after a second image name/digest prefix; keep credentials out of the build context. Create the accompanying .dockerignore before building: .gitignore does not restrict the Docker context, and only the listed runtime files are allowed into this example's context.

Create **`site/index.html`** with the following contents:

```html
<!doctype html><html lang="en"><title>My signed release</title><h1>Release one</h1></html>
```

Create **`Dockerfile`** with the following contents:

```dockerfile
FROM YOUR_REVIEWED_NGINX_IMAGE_REFERENCE
COPY site/ /usr/share/nginx/html/
```

To select a base image, pull your reviewed tag and record its digest before replacing the digest placeholder. A changing tag is not an immutable release record.

```bash
docker pull nginx:stable
docker image inspect nginx:stable --format '{{index .RepoDigests 0}}'
```

Create **`.dockerignore`** with the following contents:

```dockerignore
**
!Dockerfile
!site/
!site/index.html
```

**Check before continuing:** The Dockerfile and content belong to your new project.

### Step 2 — Create the registry and publish your first image

**Where:** Your ACR and local terminal.

Create your registry with admin credentials disabled and grant the publishing identity only the required push scope. Build, push and record the resulting digest, using your own registry and repository names. Run the Bash block in a dedicated terminal; it stops on a failed registry lookup or malformed digest instead of printing an unusable release reference.

```bash
set -euo pipefail
az login
export REGISTRY_NAME="YOUR_REGISTRY_RESOURCE_NAME"
REGISTRY_SERVER="$(az acr show --name "$REGISTRY_NAME" --query loginServer -o tsv)"
export REGISTRY_SERVER
[[ "$REGISTRY_SERVER" =~ ^[A-Za-z0-9.-]+$ ]] || { echo 'Registry lookup did not return a valid host' >&2; exit 1; }
az acr login --name "$REGISTRY_NAME"
docker build -t "$REGISTRY_SERVER/my-web:v1" .
docker push "$REGISTRY_SERVER/my-web:v1"
IMAGE_DIGEST="$(az acr repository show --name "$REGISTRY_NAME" --image my-web:v1 --query digest -o tsv)"
export IMAGE_DIGEST
[[ "$IMAGE_DIGEST" =~ ^sha256:[0-9a-fA-F]{64}$ ]] || { echo 'Missing or malformed image digest' >&2; exit 1; }
export IMAGE="$REGISTRY_SERVER/my-web@$IMAGE_DIGEST"
printf '%s\n' "$IMAGE"
```

**Check before continuing:** The selected image has an immutable registry digest.

### Step 3 — Sign with a key you control

**Where:** Your private signing workspace.

Use the complete IMAGE reference recorded in the previous step, which already contains the correct digest prefix. Create/protect the Cosign key pair in a private signing directory and distribute only the reviewed public key; if you change terminal, restore the exact recorded IMAGE value before signing.

```bash
# Keep the IMAGE value selected in the preceding step.
# Generate your signing key only in a private signing directory:
cosign generate-key-pair
cosign sign --key /private/path/cosign.key "$IMAGE"
```

**Check before continuing:** A signature is attached to your selected image and the trusted public key is pinned.

### Step 4 — Verify before selecting a release

**Where:** Your deployment host.

Verify the signature against the intended public key and inspect the image scan/provenance record. Test an unrelated public key as a negative case; verification failure must stop selection rather than fall back to an unsigned tag.

```bash
cosign verify --key /trusted/path/cosign.pub "$IMAGE"
```

**Check before continuing:** Your trusted key accepts the intended artifact and the unrelated key does not.

### Step 5 — Deploy the selected artifact and test it

**Where:** Your disposable Docker host.

Run the verified image reference on a loopback-only port and inspect the page and container image ID. No rebuild occurs between registry selection and deployment.

```bash
docker run -d --name my-release -p 127.0.0.1:8080:80 "$IMAGE"
curl -fsS http://127.0.0.1:8080/
docker inspect my-release --format '{{.Image}}'
```

**Check before continuing:** The running page and image identity match your selected release.

### Step 6 — Rehearse an exact rollback

**Where:** Your own source, registry and local host.

Build/sign a distinguishable second version and retain both digest/signature records. Verify the earlier digest again before replacing the lab container with that earlier image, then check the page; record that container rollback does not undo external database/schema changes.

**Check before continuing:** The running first-version content is restored from its retained artifact, not rebuilt source.

### Step 7 — Add CI authority and close out

**Where:** Your own GitHub repository and cleanup record.

If automating, separate build/sign/publish from release selection, use workload federation with exact repository/environment trust and a narrowly scoped identity, and bind approval to the digest. Remove only your lab deployment/images under retention policy, retaining the signing public key and recovery evidence where required.

**Check before continuing:** The reader can explain build once, sign, verify, select, deploy and roll back as distinct operations.

### Verification and your own screenshots

| Evidence | What to record | Your result |
| --- | --- | --- |
| New build | Your own files/resource settings and tool versions | Not yet recorded |
| Working path | The actual successful request, configuration or recovery result | Not yet recorded |
| Failure boundary | A meaningful denied, malformed, stale or failed case | Not yet recorded |
| Recovery / cleanup | What you restored or removed and what remains billed | Not yet recorded |

Capture your own architecture/configuration, one working result and one failure/recovery result. Keep tokens, credentials, personal records and private identifiers out of public screenshots. The architecture diagram explains the design; record your own results rather than treating it as execution evidence.

### Troubleshooting order

1. Confirm the named file, working directory and selected tool/interpreter.
2. Check the exact input and resource/account selected for the failing step.
3. Separate identity permission, network/DNS reachability and application validation.
4. Keep the actual error and reconcile an unknown write outcome before repeating it; do not widen access or repeat paid operations blindly.

The numbered steps describe a build procedure. Local syntax checks, an accepted API request, a completed hosted operation and a human verification are different evidence levels; fill in the verification table with what you actually observed.

### Official implementation references

- [docs.sigstore.dev — signing_with_containers](https://docs.sigstore.dev/cosign/signing/signing_with_containers/)
- [docs.sigstore.dev — verify](https://docs.sigstore.dev/cosign/verifying/verify/)
- [learn.microsoft.com — container-registry-authentication](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-authentication)
- [docs.docker.com — #dockerignore-files](https://docs.docker.com/build/concepts/context/#dockerignore-files)

<details>
<summary>Reference: how the existing platform implementation operates</summary>

A short walkthrough of the process, with technical instructions and evidence limits in the sections below.

1. **Build and check one version (GitHub Actions and scanner checks)** — Select the reviewed source and build the release files once. Keep the security results tied to those exact files.

2. **Retain the tested release** — Store the package with its fingerprint and source record. Preserve a verified previous release for possible recovery.

3. **Promote the same files** — Verify the selected release in a test environment before promoting it. Use the retained package rather than creating a different build at the final step.

4. **Verify or roll back deliberately** — Compare the running release with the intended version and investigate any mismatch. A rollback uses a reviewed retained package and must still satisfy compatibility and current-state checks.

</details>

## Architecture

1. **Reviewed commit** → **Build and test**.
2. **Build and test** → **Dependency / image / IaC / secret scans**.
3. **Dependency / image / IaC / secret scans** → **Trusted policy gate**.
4. **Build and test** → **Retained ZIP / digest**.
5. **Trusted policy gate** → **Exact source and artifact selection**.
6. **Retained ZIP / digest** → **Exact source and artifact selection**.
7. **Exact source and artifact selection** → **Nonproduction verification**.
8. **Nonproduction verification** → **Same bytes to production**.
9. **Retained ZIP / digest** → **Retained previous release**.

[View the illustrated project overview](../../docs/diagrams/architecture.svg).

## What Was Built

| Component | Role in plain words | Implementation |
| --- | --- | --- |
| Actual rollback guards | Bind exact source/artifact, expiring candidate, compatibility and live-state drift | [Source](reference/rollback_release.py) · [original selected tests](reference/test_rollback_release.py) |
| Deterministic package builder | Sort paths and fix ZIP metadata so identical inputs produce identical bytes. | [View code](lab/domain.py) |
| Release-file checks | Reject changed files, reports for another release, unfinished scans and findings that block release. | [View code](lab/domain.py) |
| Content-addressed release archive | Retain packages and change a small atomic release pointer instead of rebuilding. | [View code](lab/domain.py) |
| ACR and repository-specific publisher | Keep registry administrator passwords Off and limit optional GitHub publishing access to one image repository. | [View code](infra/registry.tf) |
| Private artifact storage | Use keyless, versioned archive storage with deletion protection. | [View code](infra/storage.tf) |
| Container example | Run the example with a lower-permission account in an exact, verified Python container build. | [View code](Dockerfile) |

## Proof It Works

### Extracted platform code

```bash
python -B -m unittest discover -s reference -v
```

The selected original tests run offline. [Validation](docs/VALIDATION.md) records current counts and distinguishes them from historical hosted evidence.

**Current local checks:** 12 extracted-source tests + 12 portable tests passed · 6 demonstration checks · 2 Terraform tests using simulated cloud responses.

These are dated results for this reference implementation, not live Azure/AWS deployment claims. [Test record](docs/validation-results.json) · [Evidence and limitations](docs/VALIDATION.md)

### 1. Promotion preserves the selected bytes

The local test compares the promoted package against the original. Changed bytes and stale/incomplete evidence fail before publication.

Run from the repository root:

```bash
python -B -m unittest discover -s tests -p test_domain.py -v
```

**What to look for:** The package tests reject changed bytes, wrong source, out-of-date evidence and incomplete/blocked scans.

### 2. Rollback uses the retained prior package

The demonstration re-verifies a previous archive and selects its digest. It does not rebuild the old source.

Run from the repository root:

```bash
python -B -m lab demo
```

**What to look for:** The JSON records the current and retained previous package digests and the restored selection.

### 3. The container runs under restrictions

The recorded Linux ARM64 smoke used a non-root user, no network, a read-only filesystem and dropped capabilities. This was a runtime test, not a vulnerability scan of that demonstration image.

Run from the repository root:

```bash
docker build -t delivery-reference:local .
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=16m delivery-reference:local demo
```

**What to look for:** This reproduces the recorded Linux container smoke using a portable local tag. The run is non-root and network-isolated; it is not a vulnerability scan.

### 4. Visible results

The dashboard runs the same domain code as the CLI. Desktop/mobile rendering, all three tabs, rerunning the demonstration, cross-origin write rejection and unlisted-file rejection were checked. Those local test results remain documented; proper application screenshots are deferred.

Expected access denials are successful negative tests. Cloud permissions, network connectivity and provider integrations need their own acceptance evidence.

## Security Practices

- The local policy receipt is test-only. A real release needs independently trusted scanner evidence and source-to-artifact binding.
- ACR admin credentials and storage shared keys are Off. The optional publisher uses an exact reviewed OIDC subject and repository ABAC condition.
- Trivy, Checkov, TruffleHog and ZAP have different coverage. Remaining findings stay visible; a digest or green build alone does not establish safety.

State, saved Terraform plans, private inputs and credentials are excluded through [`.gitignore`](.gitignore). The existing validation workflow is manual-only and has no cloud deployment permission.

## Run It Locally

The [command reference](docs/COMMANDS.md) includes prerequisites, Windows equivalents, focused checks and evidence notes.

Requires Python 3.12 or newer. The default demonstration uses the Python standard library. Run inside a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -B -m unittest discover -s tests -v
python -B -m lab demo
python -B -m lab serve --port 8011
```

On Windows, use `.venv\Scripts\Activate.ps1` instead of the `source` command, or run `.venv\Scripts\python.exe` directly. Open [the local workbench](http://127.0.0.1:8011), choose **Run demonstration**, then review **Validation** and **Evidence**. Stop with Ctrl+C. No cloud login, employee data or paid API request is required.

## Terraform Infrastructure

A shared-style ACR registry, keyless private release-archive storage with version protection, and an opt-in repository-specific OIDC publisher.

See the [Terraform code and validation steps](infra/README.md), [input example](infra/example.tfvars.example) and [mock plan tests](infra/tests). Cloud commissioning and any paid resources remain separate from the local demonstration.

Validate the infrastructure source without creating cloud resources:

```bash
cd infra
terraform init -backend=false
terraform fmt -check -recursive
terraform validate
terraform test
```

The tests use mock providers. Example inputs are placeholders, not deployment-ready values. Review the [integration boundaries and cost notes](infra/README.md) before any separate cloud commissioning.

## Scaling and Tradeoffs

Separate build, scan, select and publish responsibilities. Retain verified release pairs and referenced images, use trusted signing/provenance checks and avoid repeating successful jobs when only one stage fails.

See [strengths, weaknesses and tradeoffs](docs/SCALING.md) for the detailed decisions.

## Skills Demonstrated

- GitHub Actions and artifact promotion
- Container packaging and runtime restrictions
- Vulnerability/secret/IaC scan integration
- OIDC and repository-specific publishing
- Verified rollback and release traceability

## Troubleshooting Lessons

Moving tests to another runner did not fix exhausted artifact storage. Recovery preserved verified packages and their dependencies before removing selected older copies. [Read the incident, evidence and verification](docs/LESSONS-LEARNED.md).

## Project Guides

| Guide | What you will find |
| --- | --- |
| [Command reference](docs/COMMANDS.md) | Copy the commands, understand their purpose and check expected results |
| [Implementation walkthrough](docs/WALKTHROUGH.md) | Follow the processing path and code |
| [Architecture](docs/ARCHITECTURE.md) | Understand service and identity boundaries |
| [Terraform](infra/README.md) | Read the resource map, input examples and integration steps |
| [Validation evidence](docs/VALIDATION.md) | See the test dates, results and limits |
| [Operations and troubleshooting](docs/OPERATIONS.md) | Diagnose failures and recover safely |
| [Security and privacy](SECURITY.md) | Review access, secrets and publication controls |
| [Scaling and tradeoffs](docs/SCALING.md) | Understand the costs of each design choice |
| [References](docs/REFERENCES.md) | See technical sources and presentation inspiration |

## Repository Map

`reference/` contains extracted implementation logic and original selected tests.

```text
infra/               Terraform source, example inputs and mock plan tests
lab/                 Working reference implementation and loopback dashboard
tests/               Positive, negative and recovery cases
docs/                Architecture, walkthrough, evidence and operating guide
.github/workflows/   Manual-only contract validation; no cloud deployment
```

## Cost and Cleanup

The default local demo creates only temporary local state and makes no paid calls. Cloud examples are separate opt-in source and can create billable resources if an operator applies them. No automated deployment or destruction is configured. Use `git status --short --ignored` before cleanup; remove only your own `.venv` or disposable lab output. Never copy real state files, tokens or employee documents into this repository.
