# Terraform infrastructure

A shared-style ACR registry, keyless private release-archive storage with version protection, and an opt-in repository-specific OIDC publisher.

These configurations adapt the same resource boundaries used in the author's workforce/operations platform. Names and input examples are neutral; no environment state, backend, import block, secret or production identifier is included. Each folder is a standalone reference root, not a command to adopt an existing production resource into new state.

## Code map

| File | Purpose |
| --- | --- |
| [registry.tf](registry.tf) | Basic ACR with admin credentials off, ABAC mode and a conditional Repository Writer assignment for one path. |
| [storage.tf](storage.tf) | Private artifact account and ARM-created archive container, TLS, OAuth-only access and 30-day deletion protection. |
| [variables.tf](variables.tf) | Globally unique lab names, repository-path validation and explicit OIDC opt-in. |
| [tests/delivery.tftest.hcl](tests/delivery.tftest.hcl) | No publisher by default, no shared storage keys/registry admin and rejection of missing trust. |
| [versions.tf](versions.tf) | Exact provider versions; lock file records provider checksums. |
| [example inputs](example.tfvars.example) | Reviewable inputs with placeholders; never actual tenant values. |

## Validate locally without a cloud deployment

```bash
terraform init -backend=false
terraform fmt -check -recursive
terraform validate
terraform test
```

The `.tftest.hcl` files use mock providers and plan commands. They do not authenticate to Azure, create resources or mutate Entra. Provider initialization downloads provider packages; it is not an infrastructure deployment. No automatic Terraform apply is included in GitHub Actions. The existing workflow remains manual-only to avoid unnecessary Actions usage.

The `.tfvars.example` file is not loaded automatically. It contains placeholders and is not ready for a real plan. Leave real `.tfvars`, backend/state, saved plans and credentials outside Git. If you separately deploy a lab, review exact subscription/tenant, names, complete saved plan, permissions, network route, costs and cleanup first. Use a protected remote backend with Entra authentication; this public root deliberately supplies no organization backend.

## Integration boundaries

GitHub environments, exact token subject, runner routing, image builds, image signatures, trusted public-key binding, release receipts and actual archive upload are separate. The archive account remains private; prove runner DNS/network access and assign only the required container data role before publishing. This root does not deploy API/web or configure a universal Azure admission controller.

## Security and activation

The optional publisher gets Repository Writer only for the configured repository through an ABAC condition. It does not get Owner, Contributor, registry-wide AcrPush, artifact-container access or delete authority. ACR uses its authenticated public endpoint in this Basic reference; public reachability is not anonymous pull permission. Additional private endpoints require a separately reviewed SKU/network design.

## Cost, retention and cleanup

The ACR registry and retained artifacts can be billed if applied, even when publisher trust is off. Blob versioning and soft deletion retain bytes. No retention policy deletes images because rollback references must be inventoried first.

Mock-test cleanup is entirely local. A real destroy is a separate reviewed action against the correct lab state; never run it against copied production state or shared resources. Payroll deletion protection in the identity example intentionally prevents a casual destroy of that group. Retire grants/trust and inventory retained recovery artifacts before removing a real lab.

## Strengths and tradeoffs

Repository-permissions limited to the required resources are narrower than registry-wide push grants but require the correct ABAC registry mode and exact trust. Versioned archives support recovery; they are not legal-hold/WORM immutability. AzureRM 4.81.0 is pinned here because it supports the registry mode used by the source platform; the networking root uses its own reviewed version.

## Resource inventory

| Terraform resource type | Local name | Definition |
| --- | --- | --- |
| `azurerm_resource_group` | `lab` | [main.tf](main.tf) |
| `azurerm_container_registry` | `images` | [registry.tf](registry.tf) |
| `azurerm_user_assigned_identity` | `publisher` | [registry.tf](registry.tf) |
| `azurerm_federated_identity_credential` | `publisher` | [registry.tf](registry.tf) |
| `azurerm_role_assignment` | `repository_writer` | [registry.tf](registry.tf) |
| `azurerm_storage_account` | `data` | [storage.tf](storage.tf) |
| `azapi_resource` | `containers` | [storage.tf](storage.tf) |

## Official references

- [Terraform test command and mock providers](https://developer.hashicorp.com/terraform/cli/commands/test)
- [AzureRM provider documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure Registry repository permissions](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-rbac-abac-repository-permissions)

See [project architecture](../docs/ARCHITECTURE.md) and [validation evidence](../docs/VALIDATION.md) for the separate application/reference boundaries.
