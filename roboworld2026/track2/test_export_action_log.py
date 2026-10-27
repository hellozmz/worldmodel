#!/usr/bin/env python3
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from roboworld2026.track2.export_action_log import export


class ExportActionLogTests(unittest.TestCase):
    def test_package_exact_coverage_and_official_contract(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "actions"
            output = Path(folder) / "submission.zip"
            source.mkdir()
            (source / "val_seen.jsonl").write_text(
                json.dumps({"episode_id": "2", "actions": ["MOVE_FORWARD", "STOP"]}) + "\n"
                + json.dumps({"episode_id": "1", "actions": ["TURN_LEFT", "STOP"]}) + "\n",
                encoding="utf-8",
            )
            (source / "val_unseen.jsonl").write_text(
                json.dumps({"episode_id": "1", "actions": ["STOP"]}) + "\n",
                encoding="utf-8",
            )
            export(source, output, 2, 1)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), {"val_seen.json", "val_unseen.json"})
                payload = json.loads(archive.read("val_seen.json"))
                self.assertEqual([row["episode_id"] for row in payload["episodes"]], ["1", "2"])

    def test_missing_stop_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "actions"
            source.mkdir()
            (source / "val_seen.jsonl").write_text(
                json.dumps({"episode_id": "1", "actions": ["MOVE_FORWARD"]}) + "\n",
                encoding="utf-8",
            )
            (source / "val_unseen.jsonl").write_text(
                json.dumps({"episode_id": "1", "actions": ["STOP"]}) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "require STOP"):
                export(source, Path(folder) / "bad.zip", 1, 1)


if __name__ == "__main__":
    unittest.main()
