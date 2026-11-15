# Operations and troubleshooting

**Terms used here:** A digest is a file or container fingerprint used to confirm the exact version. An artifact is a file produced for a release, such as an application ZIP or container image.

## Start and stop

Run unit tests, then start the loopback dashboard with `python -B -m lab serve`. Stop with Ctrl+C. Each demonstration uses disposable test-only state; running it twice does not send messages or change a cloud resource.

## Diagnose by failure stage

| Symptom | Check and next action |
| --- | --- |
| Gate says source mismatch | Compare the selected commit and artifact manifest; never relabel a receipt to make it match. |
| Image build times out during apt | Distinguish network/package mirror delay from application test failure. Retry only the failed job after checking its stage; do not rerun all passing jobs. |
| Report has no blocking vulnerabilities | Confirm package coverage, scanner/database freshness and exit status. Empty or partial output is not a pass. |
| Rollback candidate is missing | Stop before touching production. Recover the retained verified package; do not substitute an unreviewed rebuild. |

## Cleanup

Default demos use managed temporary directories and close their own database handles. Do not run blanket recursive cleanup against a shared checkout. Inspect `git status --short --ignored`, stop the local server and remove only artifacts you created. Cloud resource cleanup is a separate reviewed operation and is never triggered by this repository's CI.

## Evidence to keep

Retain source commit, test command/exit status, tool versions and safe error stage. For a real release, also retain exact package/image digest and the restored operating state. Do not retain credentials, bearer tokens or employee data in public artifacts.
