# Validation and evidence limits

| Check | Observed result |
| --- | --- |
| Static recipe contracts | Base/package/lock version alignment, final verification target and context allowlist checked; not an image build. |
| Original Node import/journal/timing tests | 18 passed, no skips. |
| Pure image-selection guard tests | Six passed. |
| Fictional import demo | Previewed, committed, then unchanged on repeat; no network requests. |
| Fictional image-selection demo | Prepared a change while keeping Manual mode and worker Off; no Azure requests or job start. |
| Locked public dependency install | Completed with package scripts and browser downloads disabled. |
| Local installed-browser smoke | Passed in local Edge with zero external requests; Windows does not verify the Linux user. |
| Terraform format/validate/mock cases | Formatting and validation passed; three simulated cases passed. |
| Preview, links, workflow and secret scan | Workflow lint and publishable-file secret scan passed; all three preview tabs and 390-pixel mobile layout passed with no browser errors or external requests. |
| Linux container build and image scan | Not performed; installed Docker CLI found, Linux engine unreachable. |
| Registry publication and Azure deployment | Not performed. |

The root browser check is a fictional static page. The original production smoke reference checks additional synthetic browser/MFA and journal behavior, but its full private dependency set is not reproduced or newly accepted here.

The image-selection examples do not verify a real signature or establish original build provenance. Those are separate parts of the platform's reviewed release process. No provider sign-in, report download, paid message, employee action, cloud start or hosted Actions dispatch occurred for this project.

Selected unit tests passed once. They are repeated only if a related code change or failure needs verification; historical platform results are not relabelled as a new public deployment.

## Troubleshooting documentation review — November 7, 2026

Added a README incident summary and a linked historical lessons guide, checking the account against the maintained source records. Documentation checks covered local links, complete incident fields, identifying-information patterns, whitespace and preservation of the existing four-step walkthrough. Shared incidents link to the relevant project details; unresolved causes remain explicit.

This was an editorial update. Application code, tests, Terraform, images, workflow definitions and cloud settings were not changed. Existing functional test counts and screenshots above retain their original scope and dates; no application suite, live scan, paid image request, recovery rehearsal or GitHub Actions run was executed for this documentation pass.
