# Different scanners answer different questions

**Terms used here:** A digest is a file or container fingerprint used to confirm the exact version. Provenance means the record of where a release came from and how it was produced.

| Tool | What it examines | Important limit |
| --- | --- | --- |
| Trivy | Container OS packages, language dependencies, SBOMs and misconfiguration | Needs fresh advisory data and correct package/image coverage |
| Checkov | Terraform and other infrastructure definitions against policy rules | Static source findings are not direct proof of deployed state |
| TruffleHog | Potential exposed credentials in source/history | Public package hashes may look secret-like; verify rather than blanket-ignore |
| ZAP | HTTP behavior, headers and web weaknesses; authenticated coverage when configured | A passive bounded route sample is not an active whole-application penetration test |

The operational platform used dated reports, exact finding identities and tests that existing behavior still works. A dependency patch was tested through its actual consumer where possible, rather than forced onto an incompatible major. Remaining findings stayed visible; an expired baseline was not silently renewed.

The Dockerfile is digest-pinned and runs as a numeric non-root user. To validate locally:

```bash
docker build -t delivery-reference:local .
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=16m delivery-reference:local demo
trivy image --scanners vuln --severity HIGH,CRITICAL --exit-code 1 delivery-reference:local
```

Building the image is not a vulnerability scan. Save the scanner/database versions and exact image digest with a dated result. The reference receipt in `lab/domain.py` is test-only and does not replace a real scanner report, signature verification or a trusted provenance attestation. No scanner result grants cloud-deployment authority.
