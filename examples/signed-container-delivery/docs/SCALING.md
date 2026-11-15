# Scaling, strengths and tradeoffs

**Terms used here:** A digest is a file or container fingerprint used to confirm the exact version. An artifact is a file produced for a release, such as an application ZIP or container image.

## When the workload grows

Separate build, scan, select and publish jobs with minimum-permission identities. Use reusable workflows and dependency caching without sharing secrets across trust boundaries. Retain several verified rollback pairs and protect referenced images from registry purge. Scope scans to owned inputs, but run periodic full inventory checks. At larger scale use signed attestations, verified trusted workflow identity, an artifact registry and an independently enforced deployment gate.

## Design choices

| Choice | Strength, weakness and tradeoff |
| --- | --- |
| Build once / promote unchanged | Reduces environmental rebuild differences. Requires trustworthy how long release files are kept and source-to-package evidence. |
| Strict release gate | Stops missing or blocking evidence early. Policy freshness and emergency recovery need documented procedures. |
| Digest-pinned containers | Makes selection immutable. A digest does not prove the image is safe, signed or built by the expected workflow. |
| Broad scanning | Finds different defect classes. Coverage overlaps and false positives require review and prioritization, ownership and expiry dates rather than blanket exclusions. |

## Operating measures

Measure throughput, oldest pending work, duplicate/rejected operations, failure stage and recovery duration. Tie alerts to an operator action. Do not infer service availability from an old successful import or infer delivery from provider acceptance.

Start with measured load and an explicit service objective. Increase concurrency only after checking provider quotas, database contention, per-person ordering and recovery behavior. Horizontal scaling requires a shared durable store; independent in-memory or SQLite processes are not a distributed coordination system.
