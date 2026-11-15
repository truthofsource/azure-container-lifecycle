"""Extracted platform rollback checks. Offline only; no publisher or cloud adapter."""
import datetime as dt
import hashlib,json,re
from pathlib import Path
REPOSITORY="example/workforce-platform"
WORKFLOW=".github/workflows/workforce-production-rollback.yml"
REF_KEYS={"sourceSha","sha256","migrationSetSha256"}
CONTRACT="workforce-168-browser-w4-private-records-v1"
TTL_SECONDS=3600
def require(ok, code):
    if not ok:
        raise ValueError(code)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode()).hexdigest()

def validate_api_content(comparison, policy):
    require(policy.get("activeApiIdentity") == "verified-archive-filesystem-tree-v1",
            "api_filesystem_identity_not_reviewed")
    require(comparison.get("fileContentsMatch") is True
            and comparison.get("directoryTreeMatch") is True, "active_api_filesystem_mismatch")

def validate_api_storage(storage, expected_url):
    require(isinstance(storage, dict) and storage.get("type") == "blobContainer"
            and isinstance(storage.get("value"), str)
            and storage["value"].rstrip("/") == expected_url
            and isinstance(storage.get("authentication"), dict)
            and storage.get("authentication", {}).get("type") == "SystemAssignedIdentity",
            "api_deployment_storage_mismatch")

def timestamp(value):
    require(isinstance(value, str) and value.endswith("Z"), "invalid_timestamp")
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))

def utc(value):
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")

def identity(value, app):
    require(isinstance(value, dict) and set(value) == REF_KEYS, "invalid_release_fields")
    require(isinstance(value["sourceSha"], str) and re.fullmatch("[0-9a-f]{40}", value["sourceSha"]), "invalid_source")
    require(isinstance(value["sha256"], str) and re.fullmatch("[0-9a-f]{64}", value["sha256"]), "invalid_digest")
    migration = value["migrationSetSha256"]
    require(isinstance(migration, str) and (bool(re.fullmatch("[0-9a-f]{64}", migration))
                                          if app == "api" else migration == ""), "invalid_migration_digest")
    return value

def request(value):
    require(isinstance(value, dict) and set(value) == {"component", "target", "current", "reason"}, "invalid_request")
    component = value["component"]
    require(component in ("api", "web", "both"), "invalid_component")
    selected = {"api", "web"} if component == "both" else {component}
    require(isinstance(value["current"], dict) and set(value["current"]) == {"api", "web"}, "current_pair_required")
    require(isinstance(value["target"], dict) and set(value["target"]) == selected, "invalid_target_pair")
    reason = value["reason"]
    require(isinstance(reason, str) and 8 <= len(reason) <= 300
            and all(32 <= ord(c) < 127 for c in reason), "invalid_incident_reason")
    for refs in (value["current"], value["target"]):
        for app, ref in refs.items():
            identity(ref, app)
    require(any(value["current"][app] != value["target"][app] for app in selected), "rollback_is_noop")
    require(len({v["sourceSha"] for v in value["target"].values()}) == 1, "pair_source_must_match")
    return value

def compatibility(spec, policy):
    require(policy.get("schemaVersion") == 1 and policy.get("maximumLedgerVersion") == 168, "unreviewed_schema_policy")
    resulting = {**spec["current"], **spec["target"]}
    for refs in (spec["current"], resulting):
        contracts = []
        for app, ref in refs.items():
            matches = [r for r in policy.get(app, []) if {k: r.get(k) for k in REF_KEYS} == ref]
            require(len(matches) == 1 and type(matches[0].get("acceptedProductionRunId")) is int
                    and matches[0]["acceptedProductionRunId"] > 0, "release_contract_not_reviewed")
            contracts.append(matches[0].get("contract"))
        require(contracts == [CONTRACT, CONTRACT], "api_web_contract_incompatible")
    return resulting

def validate_snapshot(value, refs, policy):
    require(set(value) == {"bindings", "services", "sql", "runtimeConfigSha256", "apiBindingHash"}, "invalid_snapshot")
    require(set(value["bindings"]) == {"api", "web"} and value["bindings"] == refs, "active_release_drift")
    require(re.fullmatch("[0-9a-f]{64}", value["runtimeConfigSha256"] or ""), "invalid_runtime_config")
    require(isinstance(value["apiBindingHash"], str) and re.fullmatch("[0-9a-f]{64}", value["apiBindingHash"]), "invalid_api_binding")
    services = value["services"]
    require(set(services) == {"api", "scanner", "directory"}, "invalid_service_scope")
    for name, service in services.items():
        require(set(service) == {"settingsHash", "identityHash", "storageHash", "enabled", "state"}, "invalid_service_snapshot")
        require(type(service["enabled"]) is bool and service["state"] in ("Running", "Stopped", "Disabled"), "unexpected_service_power_state")
        if name == "api":
            require(service["enabled"] is True and service["state"] == "Running", "unexpected_api_power_state")
        for key in ("settingsHash", "identityHash", "storageHash"):
            require(isinstance(service[key], str) and re.fullmatch("[0-9a-f]{64}", service[key]), "invalid_service_fingerprint")
    validate_sql(value["sql"], policy)

def validate_sql(sql, policy):
    require(policy.get("schemaVersion") == 1 and policy.get("maximumLedgerVersion") == 168, "unreviewed_schema_policy")
    require(set(sql) == {"versions", "samMode", "permissionChecks", "openSamAttempts"}, "invalid_sql_evidence")
    validate_ledger(sql["versions"], policy, "production")
    require(sql["samMode"] == "browser", "sam_execution_mode_incompatible")
    require(type(sql["openSamAttempts"]) is int and sql["openSamAttempts"] >= 0, "invalid_claim_evidence")
    checks = sql["permissionChecks"]
    require(isinstance(checks, dict) and all(type(v) is bool for v in checks.values()), "invalid_permission_evidence")
    require(checks == {"signedFormsRead": True, "samAttemptsRead": True, "oigEvidenceRead": True,
                       "signedFormsDeleteDenied": True}, "runtime_grants_incompatible")

def validate_ledger(versions, policy, environment):
    expected = policy.get("ledgerBaselines", {}).get(environment)
    require(environment in ("production", "nonproduction")
            and policy.get("maximumLedgerVersion") == 168
            and isinstance(expected, list) and expected
            and isinstance(versions, list) and versions == expected
            and all(isinstance(v, str) and re.fullmatch(r"\d{3}_[a-z0-9_]+", v) for v in versions),
            "schema_ledger_incompatible")
    ids = [int(v[:3]) for v in versions]
    require(ids == sorted(set(ids)) and ids[0] == 1 and ids[-1] == 168,
            "schema_ledger_incompatible")

def stable_snapshot(value):
    # Claims can finish normally between preparation and execution. Their count
    # is evidence, not an instruction to stop workers or invalidate safe readers.
    result = json.loads(json.dumps(value))
    result["sql"].pop("openSamAttempts")
    return result

def prepare(spec, snapshot, policy, run_id, tooling_sha, now, tools_digest):
    request(spec)
    compatibility(spec, policy)
    validate_snapshot(snapshot, spec["current"], policy)
    require(type(run_id) is int and run_id > 0 and re.fullmatch("[0-9a-f]{40}", tooling_sha), "invalid_preparation_run")
    require(re.fullmatch("[0-9a-f]{64}", tools_digest), "invalid_tooling_digest")
    return {"schemaVersion": 1, "repository": REPOSITORY, "workflow": WORKFLOW,
            "runId": run_id, "toolingSha": tooling_sha, "toolingHash": tools_digest,
            "preparedAtUtc": utc(now), "expiresAtUtc": utc(now + dt.timedelta(seconds=TTL_SECONDS)),
            "request": spec, "baseline": snapshot, "baselineHash": digest(stable_snapshot(snapshot)),
            "policyHash": digest(policy), "productionAuthorization": False}

def candidate(value, expected_digest, run, now, tools_digest, policy, *, observation_only=False):
    require(isinstance(value, dict) and set(value) == {"schemaVersion", "repository", "workflow", "runId",
            "toolingSha", "toolingHash", "preparedAtUtc", "expiresAtUtc", "request", "baseline",
            "baselineHash", "policyHash", "productionAuthorization"}, "invalid_candidate_fields")
    require(digest(value) == expected_digest, "candidate_digest_mismatch")
    require(value["schemaVersion"] == 1 and value["productionAuthorization"] is False, "candidate_cannot_authorize")
    require(value["repository"] == REPOSITORY and value["workflow"] == WORKFLOW, "candidate_scope_mismatch")
    require(run.get("id") == value["runId"] and run.get("path") == WORKFLOW
            and run.get("status") == "completed" and run.get("conclusion") == "success"
            and run.get("event") == "workflow_dispatch" and run.get("head_branch") == "main"
            and run.get("head_sha") == value["toolingSha"] and run.get("run_attempt") == 1
            and run.get("repository", {}).get("full_name") == REPOSITORY
            and run.get("head_repository", {}).get("full_name") == REPOSITORY, "untrusted_preparation_run")
    start, end = timestamp(value["preparedAtUtc"]), timestamp(value["expiresAtUtc"])
    require(start <= now and (observation_only or now <= end) and (end-start).total_seconds() == TTL_SECONDS, "candidate_expired_or_future")
    require(value["toolingHash"] == tools_digest and value["policyHash"] == digest(policy), "rollback_tooling_changed")
    request(value["request"])
    compatibility(value["request"], policy)
    validate_snapshot(value["baseline"], value["request"]["current"], policy)
    require(value["baselineHash"] == digest(stable_snapshot(value["baseline"])), "baseline_digest_mismatch")
    return value

def check_drift(plan, live, policy):
    validate_snapshot(live, plan["request"]["current"], policy)
    require(digest(stable_snapshot(live)) == plan["baselineHash"], "live_state_changed_reprepare")

def check_after(plan, live, policy):
    refs = compatibility(plan["request"], policy)
    validate_snapshot(live, refs, policy)
    if "api" not in plan["request"]["target"]:
        require(live["apiBindingHash"] == plan["baseline"]["apiBindingHash"], "unselected_api_binding_changed")
    require(live["services"] == plan["baseline"]["services"], "service_settings_or_identity_changed")
    require(live["runtimeConfigSha256"] == plan["baseline"]["runtimeConfigSha256"], "destination_configuration_changed")
    require(stable_snapshot(live)["sql"] == stable_snapshot(plan["baseline"])["sql"], "sql_contract_changed")
