# Build your own from scratch: Azure Container Lifecycle

Your own browser-worker image, local execution evidence, registry artifact and manual Azure Container Apps Job.

Start with a new folder, your own files and your own accounts. The numbered steps below describe the build; no portfolio repository checkout is required. The existing implementation/evidence elsewhere in this repository is a separate reference, not a claim that your new build has already passed.

## Prerequisites

Node/npm, Docker with a Linux engine, Azure CLI and an Azure subscription. This worker uses harmless built-in HTML; it does not connect to CareBridge or reuse any provider session.

Use Bash on Linux/macOS/WSL for Bash blocks and PowerShell for PowerShell blocks. Select the tool versions supported by the official sources below, record the versions you actually install and retain generated dependency locks. Cloud resources, scanner downloads, logs and external AI calls can create costs; review the stated scope before enabling them.

## Create your project folder

Choose a new folder name. These first commands create a blank project; an optional `git init` gives it its own history. Create parent directories in your editor when a later step introduces a nested file.

```bash
mkdir my-azure-container-lifecycle
cd my-azure-container-lifecycle
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

## Step 1 — Create the worker source and dependency lock

**Where:** Your new folder.

Initialize your own npm package, install an exact resolved Playwright version and create worker.mjs below. Real export workers automate approved report retrieval; this standalone worker demonstrates the browser/container mechanics without a provider login.

```bash
npm init -y
npm install --save-exact playwright
```

Create **`worker.mjs`** with the following contents:

```javascript
import {chromium} from 'playwright';
import {mkdir, writeFile} from 'node:fs/promises';
await mkdir('out', {recursive: true});
const browser = await chromium.launch({args: ['--disable-dev-shm-usage']});
try {
  const page = await browser.newPage();
  await page.route('**/*', route => route.abort());
  await page.setContent('<h1>My export</h1><table><tr><td>LAB-001</td><td>Ready</td></tr></table>');
  const rows = await page.locator('tr').allTextContents();
  await writeFile('out/rows.json', JSON.stringify({rows}, null, 2));
  await page.screenshot({path: 'out/export.png'});
} finally { await browser.close(); }
```

**Check before continuing:** You have your own worker source and a matching package lock.

## Step 2 — Create the Linux image recipe

**Where:** Your project folder.

Create Dockerfile below. The build installs the browsers matching the npm package and its Linux libraries; the final process runs as a non-root user. Create the accompanying .dockerignore before building: .gitignore does not restrict the Docker context, and only the listed runtime files are allowed into this example's context.

Create **`Dockerfile`** with the following contents:

```dockerfile
FROM node:22-bookworm-slim
WORKDIR /work
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts && npx playwright install --with-deps chromium
COPY worker.mjs ./
RUN mkdir -p /work/out && chown node:node /work/out
USER node
CMD ["node", "worker.mjs"]
```

Create **`.dockerignore`** with the following contents:

```dockerignore
**
!Dockerfile
!package.json
!package-lock.json
!worker.mjs
```

**Check before continuing:** The image recipe includes both the Playwright package and its browser/system dependencies.

## Step 3 — Build and run locally

**Where:** Your Docker host.

Build the image, prepare an output folder writable by your selected runtime UID, and run it without outbound networking. Review the generated rows and screenshot; do not treat a successful image build as proof that Chromium launched. This Azure job example targets linux/amd64; on another host architecture, use a compatible cross-builder/emulator and verify the target image rather than assuming a host-native build will run in Azure.

```bash
docker build --platform linux/amd64 -t my-browser-worker:lab .
mkdir -p out
docker run --rm --init --network none --cap-drop ALL --security-opt no-new-privileges   --user "$(id -u):$(id -g)" -v "$PWD/out:/work/out:rw" my-browser-worker:lab
cat out/rows.json
```

**Check before continuing:** rows.json and export.png exist from an actual browser execution.

## Step 4 — Create your own registry and publish

**Where:** Azure Portal → Container registries; then your terminal.

Create an ACR with admin access disabled and use the actual loginServer returned by Azure rather than guessing its DNS name. Push the image and form WORKER_IMAGE from that server plus the returned digest, which already includes sha256:; retain that complete reference for the manual job. Run the Bash block in a dedicated terminal; it stops on a failed registry lookup or malformed digest instead of printing an unusable release reference.

```bash
set -euo pipefail
az login
export REGISTRY_NAME="YOUR_REGISTRY_RESOURCE_NAME"
REGISTRY_SERVER="$(az acr show --name "$REGISTRY_NAME" --query loginServer -o tsv)"
export REGISTRY_SERVER
[[ "$REGISTRY_SERVER" =~ ^[A-Za-z0-9.-]+$ ]] || { echo 'Registry lookup did not return a valid host' >&2; exit 1; }
az acr login --name "$REGISTRY_NAME"
docker tag my-browser-worker:lab "$REGISTRY_SERVER/my-browser-worker:lab"
docker push "$REGISTRY_SERVER/my-browser-worker:lab"
IMAGE_DIGEST="$(az acr repository show --name "$REGISTRY_NAME" --image my-browser-worker:lab --query digest -o tsv)"
export IMAGE_DIGEST
[[ "$IMAGE_DIGEST" =~ ^sha256:[0-9a-fA-F]{64}$ ]] || { echo 'Missing or malformed image digest' >&2; exit 1; }
export WORKER_IMAGE="$REGISTRY_SERVER/my-browser-worker@$IMAGE_DIGEST"
printf '%s\n' "$WORKER_IMAGE"
```

**Check before continuing:** Your registry contains the selected image and you have its immutable digest.

## Step 5 — Create a manual job with managed pull access

**Where:** Azure Portal → Container Apps Jobs → Create.

Choose a new environment, Manual trigger and your reviewed ACR image digest. Configure a managed identity with pull access for the selected registry, bounded timeout, zero automatic retries and suitable CPU/memory; provider credentials are not needed by this example. Copy the complete WORKER_IMAGE value from the previous step; do not prepend another sha256: to it.

**Check before continuing:** The job references your digest and is not enabled on a recurring schedule.

## Step 6 — Run and inspect one execution

**Where:** Your job → Start; execution history/logs.

Start the job once and inspect its terminal status and logs. Local out files are ephemeral in the cloud; if you need retained cloud exports, first add a private storage adapter, workload identity permission and an output/idempotency contract.

**Check before continuing:** You have real container-job execution evidence without claiming that ephemeral files are a durable export pipeline.

## Step 7 — Record the lifecycle and clean up

**Where:** Your evidence and Azure Portal.

Keep source, lockfile, image digest, scan result and execution status together. Remove your isolated job/environment/registry after reviewing retained images/logs and any other dependencies.

**Check before continuing:** You can describe source → Dockerfile → image → registry → selected job → execution.

## Verification and your own screenshots

| Evidence | What to record | Your result |
| --- | --- | --- |
| New build | Your own files/resource settings and tool versions | Not yet recorded |
| Working path | The actual successful request, configuration or recovery result | Not yet recorded |
| Failure boundary | A meaningful denied, malformed, stale or failed case | Not yet recorded |
| Recovery / cleanup | What you restored or removed and what remains billed | Not yet recorded |

Capture your own architecture/configuration, one working result and one failure/recovery result. Keep tokens, credentials, personal records and private identifiers out of public screenshots. The architecture diagram explains the design; record your own results rather than treating it as execution evidence.

## Troubleshooting order

1. Confirm the named file, working directory and selected tool/interpreter.
2. Check the exact input and resource/account selected for the failing step.
3. Separate identity permission, network/DNS reachability and application validation.
4. Keep the actual error and reconcile an unknown write outcome before repeating it; do not widen access or repeat paid operations blindly.

The numbered steps describe a build procedure. Local syntax checks, an accepted API request, a completed hosted operation and a human verification are different evidence levels; fill in the verification table with what you actually observed.

## Official implementation references

- [playwright.dev — docker](https://playwright.dev/docs/docker)
- [learn.microsoft.com — jobs](https://learn.microsoft.com/en-us/azure/container-apps/jobs)
- [learn.microsoft.com — container-registry-authentication-managed-identity](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-authentication-managed-identity)
- [docs.docker.com — #dockerignore-files](https://docs.docker.com/build/concepts/context/#dockerignore-files)
