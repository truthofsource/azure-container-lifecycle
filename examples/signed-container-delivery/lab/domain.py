"""Portable reference for immutable promotion and verified rollback."""

import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
import time
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            if (
                not re.fullmatch(
                    r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)*\.[A-Za-z0-9]+", name
                )
                or ".." in name
            ):
                raise ValueError("Archive path is outside the allowed package layout")
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return output.getvalue()


def verify(package, receipt, source, now=None):
    """Receipt must come from an independently trusted scanner, not the candidate."""
    now = int(time.time()) if now is None else now
    if receipt.get("schema") != 1 or receipt.get("policy") != "dependencies-v1":
        raise ValueError("Missing or unexpected policy evidence")
    if receipt.get("digest") != digest(package) or receipt.get("source") != source:
        raise ValueError("Source or artifact mismatch")
    if (
        type(receipt.get("checked_at")) is not int
        or not 0 <= now - receipt["checked_at"] <= 86400
    ):
        raise ValueError("Policy evidence is stale or from the future")
    if (
        receipt.get("status") != "complete"
        or type(receipt.get("fixable_high_critical")) is not int
        or receipt["fixable_high_critical"] != 0
    ):
        raise ValueError("Incomplete scan or blocking dependency findings")
    return digest(package)


def promote(root, package, receipt, source, now=None):
    release_id = verify(package, receipt, source, now)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    # Content-addressed immutable storage; concurrent identical writers agree.
    target = root / (release_id + ".zip")
    try:
        with target.open("xb") as file:
            file.write(package)
    except FileExistsError:
        if target.read_bytes() != package:
            raise ValueError("Retained archive failed integrity")
    # Only the small pointer changes; never rebuild the selected ZIP.
    handle, name = tempfile.mkstemp(prefix=".current-", dir=root)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            json.dump({"digest": release_id, "source": source}, file)
            file.flush()
            os.fsync(file.fileno())
        os.replace(name, root / "current.json")
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return release_id


def demo():
    now = int(time.time())
    prior = build({"app/index.txt": b"previous reviewed release"})
    current = build({"app/index.txt": b"current reviewed release"})
    receipt = lambda data, source: {
        "schema": 1,
        "policy": "dependencies-v1",
        "source": source,
        "digest": digest(data),
        "checked_at": now,
        "status": "complete",
        "fixable_high_critical": 0,
    }
    checks = []
    checks.append(
        {
            "name": "Deterministic package bytes",
            "passed": current == build({"app/index.txt": b"current reviewed release"}),
            "detail": "Sorted paths, fixed ZIP timestamps and permissions",
        }
    )
    with tempfile.TemporaryDirectory() as folder:
        old_id = promote(folder, prior, receipt(prior, "source-001"), "source-001", now)
        new_id = promote(
            folder, current, receipt(current, "source-002"), "source-002", now
        )
        checks.append(
            {
                "name": "Promotion preserves exact package bytes",
                "passed": (Path(folder) / (new_id + ".zip")).read_bytes() == current,
                "detail": "Same reviewed ZIP copied; no rebuild",
            }
        )
        for name, data, proof in [
            (
                "Tampered artifact is rejected",
                current + b"x",
                receipt(current, "source-002"),
            ),
            (
                "Blocking findings stop publication",
                current,
                {**receipt(current, "source-002"), "fixable_high_critical": 1},
            ),
            (
                "Stale evidence is rejected",
                current,
                {**receipt(current, "source-002"), "checked_at": now - 86401},
            ),
        ]:
            try:
                verify(data, proof, "source-002", now)
                passed = False
            except ValueError:
                passed = True
            checks.append(
                {
                    "name": name,
                    "passed": passed,
                    "detail": "Expected policy denial observed",
                }
            )
        restored = promote(
            folder,
            (Path(folder) / (old_id + ".zip")).read_bytes(),
            receipt(prior, "source-001"),
            "source-001",
            now,
        )
        checks.append(
            {
                "name": "Rollback selects the retained prior package",
                "passed": restored == old_id,
                "detail": "Prior artifact reverified before pointer change",
            }
        )
    return {
        "checks": checks,
        "metrics": [
            {
                "label": "Rebuilds during promotion",
                "value": "0",
                "detail": "Immutable bytes retained",
            },
            {
                "label": "Policy checks",
                "value": str(len(checks)),
                "detail": "Including negative cases",
            },
            {
                "label": "Retained releases",
                "value": "2",
                "detail": "Synthetic local packages",
            },
            {
                "label": "Cloud changes",
                "value": "0",
                "detail": "Filesystem release adapter",
            },
        ],
        "records": [
            ["source-001", "Retained", old_id[:16]],
            ["source-002", "Promoted", new_id[:16]],
            ["source-001", "Restored", "Exact prior digest selected"],
        ],
    }
