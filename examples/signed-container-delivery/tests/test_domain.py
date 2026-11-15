import tempfile, time, unittest
from pathlib import Path
from lab.domain import build, digest, verify, promote


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.data = build({"app/readme.txt": b"fixture"})
        self.now = int(time.time())
        self.r = {
            "schema": 1,
            "policy": "dependencies-v1",
            "digest": digest(self.data),
            "source": "source-001",
            "checked_at": self.now,
            "status": "complete",
            "fixable_high_critical": 0,
        }

    def test_repeat_build(self):
        self.assertEqual(self.data, build({"app/readme.txt": b"fixture"}))

    def test_input_order(self):
        self.assertEqual(
            build({"app/a.txt": b"a", "app/b.txt": b"b"}),
            build({"app/b.txt": b"b", "app/a.txt": b"a"}),
        )

    def test_traversal(self):
        with self.assertRaises(ValueError):
            build({"../secret.txt": b"no"})

    def test_wrong_source(self):
        with self.assertRaises(ValueError):
            verify(self.data, self.r, "wrong-source", self.now)

    def test_tamper(self):
        with self.assertRaises(ValueError):
            verify(self.data + b"x", self.r, "source-001", self.now)

    def test_stale(self):
        with self.assertRaises(ValueError):
            verify(self.data, self.r, "source-001", self.now + 86401)

    def test_incomplete(self):
        with self.assertRaises(ValueError):
            verify(self.data, {**self.r, "status": "partial"}, "source-001", self.now)

    def test_high_finding(self):
        with self.assertRaises(ValueError):
            verify(
                self.data,
                {**self.r, "fixable_high_critical": 1},
                "source-001",
                self.now,
            )

    def test_boolean_count_rejected(self):
        with self.assertRaises(ValueError):
            verify(
                self.data,
                {**self.r, "fixable_high_critical": False},
                "source-001",
                self.now,
            )

    def test_promotion_and_retention(self):
        with tempfile.TemporaryDirectory() as folder:
            d = promote(folder, self.data, self.r, "source-001", self.now)
            self.assertEqual((Path(folder) / (d + ".zip")).read_bytes(), self.data)
            self.assertTrue((Path(folder) / "current.json").exists())

    def test_corrupt_retained_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / (digest(self.data) + ".zip")).write_bytes(b"changed")
            with self.assertRaises(ValueError):
                promote(folder, self.data, self.r, "source-001", self.now)
