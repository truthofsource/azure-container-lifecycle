import copy,datetime as dt,json,tempfile,unittest
from pathlib import Path
import rollback_release as r
NOW = dt.datetime(2026, 10, 28, 22, tzinfo=dt.timezone.utc)
API = {"sourceSha": "a" * 40, "sha256": "b" * 64, "migrationSetSha256": "c" * 64}
WEB = {"sourceSha": "d" * 40, "sha256": "e" * 64, "migrationSetSha256": ""}
OLD = {"sourceSha": "f" * 40, "sha256": "1" * 64, "migrationSetSha256": ""}
POLICY = {"schemaVersion": 1, "maximumLedgerVersion": 168,
          "ledgerBaselines": {"production": [f"{i:03}_migration" for i in range(1,169)]},
          "api": [{**API, "contract": r.CONTRACT, "acceptedProductionRunId": 123}],
          "web": [{**v, "contract": r.CONTRACT, "acceptedProductionRunId": 123} for v in (WEB, OLD)]}
SPEC = {"component": "web", "current": {"api": API, "web": WEB}, "target": {"web": OLD},
        "reason": "INCIDENT-123: restore previous reviewed web"}
SNAPSHOT = {"bindings": SPEC["current"], "runtimeConfigSha256": "2" * 64, "apiBindingHash": "8" * 64,
            "services": {k: {"settingsHash": "3" * 64, "identityHash": "4" * 64,
                             "storageHash": "5" * 64, "enabled": True, "state": "Running"}
                         for k in ("api", "scanner", "directory")},
            "sql": {"versions": [f"{i:03}_migration" for i in range(1, 169)], "samMode": "browser",
                    "openSamAttempts": 3, "permissionChecks": {"signedFormsRead": True,
                    "samAttemptsRead": True, "oigEvidenceRead": True, "signedFormsDeleteDenied": True}}}
RUN = {"id": 123, "path": r.WORKFLOW, "status": "completed", "conclusion": "success",
       "event": "workflow_dispatch", "head_branch": "main", "head_sha": "6" * 40,
       "run_attempt": 1, "repository": {"full_name": r.REPOSITORY},
       "head_repository": {"full_name": r.REPOSITORY}}


def plan():
    return r.prepare(copy.deepcopy(SPEC), copy.deepcopy(SNAPSHOT), POLICY, 123, "6" * 40, NOW, "7" * 64)


class RollbackChecks(unittest.TestCase):
    def test_reviewed_ledger_gaps_are_exact_not_inferred_from_maximum(self):
            policy=copy.deepcopy(POLICY)
            policy['ledgerBaselines']['nonproduction']=[f'{i:03}_migration' for i in range(1,169) if i not in range(2,25)]
            versions=policy['ledgerBaselines']['nonproduction']
            self.assertEqual(len(versions),145)
            self.assertTrue(versions[-1].startswith('168_'))
            r.validate_ledger(versions,policy,'nonproduction')
            for changed in (versions[:-1],sorted(versions+['002_unreviewed']),
                            ['001_renamed']+versions[1:]):
                with self.assertRaisesRegex(ValueError,'schema_ledger_incompatible'):
                    r.validate_ledger(changed,policy,'nonproduction')

    def test_readonly_candidate_roundtrip_and_target_pair(self):
            value = plan()
            self.assertFalse(value["productionAuthorization"])
            self.assertEqual(r.candidate(value, r.digest(value), RUN, NOW, "7" * 64, POLICY), value)
            self.assertEqual(r.compatibility(SPEC, POLICY), {"api": API, "web": OLD})
            self.assertEqual(len(value["baseline"]["sql"]["versions"]), 168)

    def test_arbitrary_resource_url_command_and_target_are_rejected(self):
            for key, value in (("resourceId", "/subscriptions/other"), ("sql", "DELETE X"),
                               ("zipUrl", "https://example.invalid/release.zip"), ("approved", True)):
                spec = copy.deepcopy(SPEC); spec[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError):
                    r.request(spec)
            spec = copy.deepcopy(SPEC); spec["component"] = "scanner"
            with self.assertRaises(ValueError): r.request(spec)

    def test_invalid_digest_noop_and_mixed_pair_rejected(self):
            for key in ("sha256", "sourceSha", "migrationSetSha256"):
                spec = copy.deepcopy(SPEC); spec["current"]["api"][key] = "bad"
                with self.subTest(key=key), self.assertRaises(ValueError): r.request(spec)
            spec = copy.deepcopy(SPEC); spec["target"]["web"] = WEB
            with self.assertRaisesRegex(ValueError, "noop"): r.request(spec)
            spec = copy.deepcopy(SPEC); spec["component"] = "both"; spec["target"]["api"] = API
            with self.assertRaisesRegex(ValueError, "pair_source"): r.request(spec)

    def test_unknown_archived_release_is_not_a_reviewed_contract(self):
            spec = copy.deepcopy(SPEC); spec["target"]["web"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "not_reviewed"): r.compatibility(spec, POLICY)
            policy = copy.deepcopy(POLICY); policy["web"][1]["contract"] = "old-api-collector"
            with self.assertRaisesRegex(ValueError, "incompatible"): r.compatibility(SPEC, policy)

    def test_expired_future_or_tampered_candidate_is_rejected(self):
            value = plan()
            for when in (NOW-dt.timedelta(seconds=1), NOW+dt.timedelta(seconds=3601)):
                with self.assertRaisesRegex(ValueError, "expired_or_future"):
                    r.candidate(value, r.digest(value), RUN, when, "7" * 64, POLICY)
            changed = copy.deepcopy(value); changed["request"]["reason"] = "different incident"
            with self.assertRaisesRegex(ValueError, "digest_mismatch"):
                r.candidate(changed, r.digest(value), RUN, NOW, "7" * 64, POLICY)
            value["productionAuthorization"] = True
            with self.assertRaisesRegex(ValueError, "cannot_authorize"):
                r.candidate(value, r.digest(value), RUN, NOW, "7" * 64, POLICY)

    def test_wrong_failed_forked_or_rerun_preparation_is_rejected(self):
            for key, bad in (("path", ".github/workflows/other.yml"), ("head_branch", "feature"),
                             ("status", "in_progress"), ("conclusion", "failure"), ("run_attempt", 2),
                             ("event", "pull_request"), ("head_sha", "0" * 40),
                             ("head_repository", {"full_name": "attacker/fork"})):
                run = {**RUN, key: bad}; value = plan()
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, "untrusted"):
                    r.candidate(value, r.digest(value), run, NOW, "7" * 64, POLICY)

    def test_expired_candidate_can_only_be_used_for_readonly_observation(self):
            value = plan(); later = NOW+dt.timedelta(hours=2)
            self.assertFalse(r.candidate(value, r.digest(value), RUN, later, "7"*64, POLICY,
                                         observation_only=True)["productionAuthorization"])
            with self.assertRaisesRegex(ValueError, "expired"):
                r.candidate(value, r.digest(value), RUN, later, "7"*64, POLICY)

    def test_tooling_policy_and_baseline_drift_are_rejected(self):
            value = plan()
            with self.assertRaisesRegex(ValueError, "tooling_changed"):
                r.candidate(value, r.digest(value), RUN, NOW, "0" * 64, POLICY)
            for key in ("settingsHash", "identityHash", "storageHash"):
                live = copy.deepcopy(SNAPSHOT); live["services"]["api"][key] = "0" * 64
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, "reprepare"):
                    r.check_drift(value, live, POLICY)
            live = copy.deepcopy(SNAPSHOT); live["bindings"]["web"] = OLD
            with self.assertRaisesRegex(ValueError, "active_release_drift"): r.check_drift(value, live, POLICY)

    def test_schema_mode_grants_and_power_are_not_assumed(self):
            cases = []
            for mutation in (lambda v: v["sql"]["versions"].pop(),
                             lambda v: v["sql"].update(samMode="api"),
                             lambda v: v["sql"]["permissionChecks"].update(signedFormsDeleteDenied=False),
                             lambda v: v["services"]["api"].update(state="Disabled")):
                live = copy.deepcopy(SNAPSHOT); mutation(live); cases.append(live)
            for live in cases:
                with self.assertRaises(ValueError): r.check_drift(plan(), live, POLICY)

    def test_compatible_worker_claim_completion_does_not_require_stopping_jobs(self):
            live = copy.deepcopy(SNAPSHOT); live["sql"]["openSamAttempts"] = 1
            r.check_drift(plan(), live, POLICY)
            live["bindings"] = {"api": API, "web": OLD}
            r.check_after(plan(), live, POLICY)
            live["services"]["scanner"]["enabled"] = False
            with self.assertRaises(ValueError): r.check_after(plan(), live, POLICY)

    def test_same_bytes_redeployment_is_still_binding_drift(self):
            live = copy.deepcopy(SNAPSHOT); live["apiBindingHash"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "reprepare"): r.check_drift(plan(), live, POLICY)
            live["bindings"] = {"api": API, "web": OLD}
            with self.assertRaisesRegex(ValueError, "unselected_api"): r.check_after(plan(), live, POLICY)
