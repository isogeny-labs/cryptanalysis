import hashlib
from pathlib import Path
import tempfile
import unittest

from recover_hecke_inputs import recover
from artifacts import Config, Remote, object_key


class FrozenInputRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        self.root.mkdir()
        self.store = Path(self.temporary.name) / "store"
        self.remote = Remote(Config(self.root, self.store.as_uri(), None, None, self.root / "cache", "aws"))
        self.content = b"frozen exact input\n"
        self.digest = hashlib.sha256(self.content).hexdigest()
        self.object = self.store / object_key(self.digest)
        self.object.parent.mkdir(parents=True)
        self.object.write_bytes(self.content)

    def test_recovers_exact_bytes_and_preserves_a_conflicting_present_file(self):
        relative = "experiments/fixture/input.json"
        self.assertEqual(recover(self.root, self.remote, relative, self.digest)["status"], "recovered_verified")
        target = self.root / relative
        self.assertEqual(target.read_bytes(), self.content)
        target.write_bytes(b"different archived record")
        with self.assertRaisesRegex(ValueError, "present input differs"):
            recover(self.root, self.remote, relative, self.digest)
        self.assertEqual(target.read_bytes(), b"different archived record")

    def test_refuses_a_poisoned_object_without_creating_a_destination(self):
        self.object.write_bytes(b"corrupt object under the expected key")
        relative = "experiments/fixture/input.json"
        with self.assertRaisesRegex(ValueError, "store object differs"):
            recover(self.root, self.remote, relative, self.digest)
        self.assertFalse((self.root / relative).exists())

    def test_refuses_traversal_and_symlinks_outside_the_repository(self):
        with self.assertRaisesRegex(ValueError, "must remain"):
            recover(self.root, self.remote, "experiments/../../outside", self.digest)
        (self.root / "experiments").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "must remain"):
            recover(self.root, self.remote, "experiments/outside", self.digest)


if __name__ == "__main__":
    unittest.main()
