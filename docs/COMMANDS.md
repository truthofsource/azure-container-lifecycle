# Commands and portal walkthrough

## Local checks with no cloud account

```bash
python -B scripts/check_recipe.py
npm test
npm run demo
python -B -m unittest discover -s scripts -p 'test_*.py' -v
python -B scripts/demo.py
```

The Node tests and journal demo use built-in modules. The Python checks use the standard library and fictional job records.

## Install the locked browser dependencies

```bash
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci --ignore-scripts --no-audit --no-fund
LIFECYCLE_BROWSER_CHANNEL=msedge npm run browser:smoke
```

That optional command uses an installed Edge browser for a local synthetic page. It is not Linux-container acceptance. The intended image check uses the browser already included in the pinned Playwright base.

## Build and run when a Linux Docker engine is available

```bash
docker version
docker info --format '{{.OSType}}'
docker build --platform linux/amd64 --tag carebridge-lifecycle:local .
docker run --rm --network none --shm-size=1g carebridge-lifecycle:local src/browser-smoke.mjs
docker run --rm --network none carebridge-lifecycle:local
```

The normal build targets the final verification stage. Do not select `--target runtime` and then describe the skipped build-time check as passed. The public default command finishes a fictional demo; it cannot import provider reports.

## Scan an image you actually built

```bash
trivy image --scanners vuln --format json --output image-vulnerabilities.json carebridge-lifecycle:local
trivy image --format cyclonedx --output image-sbom.cdx.json carebridge-lifecycle:local
```

Record the scanner/database age and check scan completion before interpreting findings. These are instructions, not newly observed image-scan results for this publication.

## Registry reference: separate from the local example

The following writes to a registry and was **not executed for this project**. Use only your own authorized target; never include credentials in a Dockerfile or committed configuration.

```bash
LIFECYCLE_REGISTRY=yourregistry
LIFECYCLE_TAG=reviewed-example
az acr login --name "$LIFECYCLE_REGISTRY"
docker tag carebridge-lifecycle:local "$LIFECYCLE_REGISTRY.azurecr.io/carebridge/importer:$LIFECYCLE_TAG"
docker push "$LIFECYCLE_REGISTRY.azurecr.io/carebridge/importer:$LIFECYCLE_TAG"
az acr repository show --name "$LIFECYCLE_REGISTRY" --image "carebridge/importer:$LIFECYCLE_TAG" --query digest --output tsv
```

Use the returned registry manifest digest for release selection. A local Docker image ID is a different identifier; do not substitute it for that digest. The production selection procedure requires its own trusted evidence and consumer checks rather than an arbitrary image update command.

## Simulated Terraform checks

```bash
terraform -chdir=infra init -backend=false -input=false
terraform -chdir=infra fmt -check -recursive
terraform -chdir=infra validate
terraform -chdir=infra test
```

Tests mock Azure and perform no live apply. Do not apply the fictional root to production; it neither owns the existing job nor provisions its network, registry or pull permissions.

## Azure portal: follow an existing authorized deployment

1. Open Container Registries and the relevant repository to inspect its tags and manifest digest.
2. Open the intended Container Apps Job and compare its image with that recorded digest.
3. Inspect the job's identity, registry authentication, resources and trigger settings.
4. Open execution history and logs, then compare them with the application import history.

Viewing these pages is separate from changing an image or starting an execution. Keep credentials and report contents out of screenshots.

## Open the local visual guide

```bash
python -B scripts/preview.py --port 8144
```

Open [the local guide](http://127.0.0.1:8144). Stop the server with Ctrl+C when finished.
