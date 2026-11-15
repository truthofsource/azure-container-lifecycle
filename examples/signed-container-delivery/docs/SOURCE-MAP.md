# Source map and deliberate adaptations

**Terms used here:** A fixture is test data or a test setup used instead of real business records.

The selected implementation was reviewed November 6, 2026. Hashes identify private source inputs without publishing that private repository or its history. Example identities and labels preserve comparisons, not live authorization.

| Public file | Original implementation area | Adaptation |
| --- | --- | --- |
| [reference/rollback_release.py](../reference/rollback_release.py) | `scripts/rollback_release.py` | Actual offline functions; omit repository-file hash adapter and unused native-reviewer branch; historical schema-168 contract retained |
| [reference/test_rollback_release.py](../reference/test_rollback_release.py) | `scripts/test_rollback_release.py` | Retain 12 original offline tests; omit native-reviewer, live operations, repo inventory and SQL-helper integration cases |

The retained source tests replace one private ledger-file lookup with an explicit fictional 145-entry gap fixture. Schema 168 is a historical contract, not the current production ledger. Publishing/CLI adapters and actual release inventory are not included.

[Machine source hashes](source-map.json) · [Validation and limits](VALIDATION.md)

The source map records where the Terraform and other reference files came from. The reusable examples still need their own connection tests and are not complete copies of the deployed setup.
