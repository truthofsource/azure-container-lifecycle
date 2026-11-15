# Sources, adaptation and presentation credits

## Source of the engineering story

The architecture and operating lessons come from an Azure workforce/operations platform I built and operated. This public adaptation removes organization names, product branding, tenant/subscription/resource identifiers, private hostnames, employee records and secret material. Only curated reusable patterns are published; no private repository history is copied.

The loopback demonstration remains a local reference. Selected implementation source and original tests are now included separately, with each extraction/adaptation recorded in SOURCE-MAP.md. Screenshots show their actual local execution with test-only fixtures. Cloud integration or historical acceptance is not inferred from those screenshots.

## Technical references

- [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Trivy documentation](https://trivy.dev/latest/docs/)
- [Checkov documentation](https://www.checkov.io/)
- [ZAP baseline scan](https://www.zaproxy.org/docs/docker/baseline-scan/)

## Presentation inspiration

- [Azure DevOps / AWS federation lab](https://github.com/Lia-Bing0/azure-devops-aws-federation-lab)
- [Multi-cloud IAM and NHI governance](https://github.com/JustinGallimore/multi-cloud-iam-nhi-governance)

These repositories informed the business-scenario, architecture, walkthrough and screenshot presentation. Their source code and screenshots were not copied. This project's code and assets are separately authored or adapted from my own platform material.

- [Network Security and Traffic Analysis](https://github.com/fabrizio-mastrogiovanni/Network-Security---Traffic-Analysis) — inspiration for the business-problem, solution, component-table and numbered-evidence presentation. Wording, implementation and screenshots in this project are its own.
