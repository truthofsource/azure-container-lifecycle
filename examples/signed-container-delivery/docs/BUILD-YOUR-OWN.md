# Build your own from scratch: Secure Container Delivery And Rollback

Your own built image, registry digest, signature verification and deployment/rollback to retained signed images.

Start with a new folder, your own files and your own accounts. The numbered steps below describe the build; no portfolio repository checkout is required. The existing implementation/evidence elsewhere in this repository is a separate reference, not a claim that your new build has already passed.

## Prerequisites

Docker, Azure CLI, Cosign, your own ACR and a disposable local deployment host. Use harmless public-lab content; image signatures can publish digest/key metadata to a transparency log.

Use Bash on Linux/macOS/WSL for Bash blocks and PowerShell for PowerShell blocks. Select the tool versions supported by the official sources below, record the versions you actually install and retain generated dependency locks. Cloud resources, scanner downloads, logs and external AI calls can create costs; review the stated scope before enabling them.

## Create your project folder

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

## Step 1 — Create a web image from your own files

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

## Step 2 — Create the registry and publish your first image

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

## Step 3 — Sign with a key you control

**Where:** Your private signing workspace.

Use the complete IMAGE reference recorded in the previous step, which already contains the correct digest prefix. Create/protect the Cosign key pair in a private signing directory and distribute only the reviewed public key; if you change terminal, restore the exact recorded IMAGE value before signing.

```bash
# Keep the IMAGE value selected in the preceding step.
# Generate your signing key only in a private signing directory:
cosign generate-key-pair
cosign sign --key /private/path/cosign.key "$IMAGE"
```

**Check before continuing:** A signature is attached to your selected image and the trusted public key is pinned.

## Step 4 — Verify before selecting a release

**Where:** Your deployment host.

Verify the signature against the intended public key and inspect the image scan/provenance record. Test an unrelated public key as a negative case; verification failure must stop selection rather than fall back to an unsigned tag.

```bash
cosign verify --key /trusted/path/cosign.pub "$IMAGE"
```

**Check before continuing:** Your trusted key accepts the intended artifact and the unrelated key does not.

## Step 5 — Deploy the selected artifact and test it

**Where:** Your disposable Docker host.

Run the verified image reference on a loopback-only port and inspect the page and container image ID. No rebuild occurs between registry selection and deployment.

```bash
docker run -d --name my-release -p 127.0.0.1:8080:80 "$IMAGE"
curl -fsS http://127.0.0.1:8080/
docker inspect my-release --format '{{.Image}}'
```

**Check before continuing:** The running page and image identity match your selected release.

## Step 6 — Rehearse an exact rollback

**Where:** Your own source, registry and local host.

Build/sign a distinguishable second version and retain both digest/signature records. Verify the earlier digest again before replacing the lab container with that earlier image, then check the page; record that container rollback does not undo external database/schema changes.

**Check before continuing:** The running first-version content is restored from its retained artifact, not rebuilt source.

## Step 7 — Add CI authority and close out

**Where:** Your own GitHub repository and cleanup record.

If automating, separate build/sign/publish from release selection, use workload federation with exact repository/environment trust and a narrowly scoped identity, and bind approval to the digest. Remove only your lab deployment/images under retention policy, retaining the signing public key and recovery evidence where required.

**Check before continuing:** The reader can explain build once, sign, verify, select, deploy and roll back as distinct operations.

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

- [docs.sigstore.dev — signing_with_containers](https://docs.sigstore.dev/cosign/signing/signing_with_containers/)
- [docs.sigstore.dev — verify](https://docs.sigstore.dev/cosign/verifying/verify/)
- [learn.microsoft.com — container-registry-authentication](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-authentication)
- [docs.docker.com — #dockerignore-files](https://docs.docker.com/build/concepts/context/#dockerignore-files)
