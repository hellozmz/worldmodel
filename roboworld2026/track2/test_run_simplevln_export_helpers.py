#!/usr/bin/env python3
import gzip
import json
from pathlib import Path
import tempfile
import unittest

from roboworld2026.track2.run_simplevln_social_export import (
    load_simplevln_instructions,
    override_instruction,
)


class RunSimpleVLNExportHelperTests(unittest.TestCase):
    def test_load_and_override_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "eval_data/r2r/val_unseen/val_unseen.json.gz"
            path.parent.mkdir(parents=True)
            payload = {
                "episodes": [
                    {"episode_id": 12, "instruction": {"instruction_text": "Exit the room."}},
                    {"episode_id": 13, "instruction": {"instruction_text": "Walk left."}},
                ]
            }
            with gzip.open(path, "wt", encoding="utf-8") as stream:
                json.dump(payload, stream)
            instructions = load_simplevln_instructions(root)
            self.assertEqual(instructions, {"12": "Exit the room.", "13": "Walk left."})
            observation = {"rgb": "unchanged", "instruction": {"text": "long HA text", "tokens": [1]}}
            result = override_instruction(observation, instructions["12"])
            self.assertEqual(result["rgb"], "unchanged")
            self.assertEqual(result["instruction"]["text"], "Exit the room.")
            self.assertEqual(result["instruction"]["tokens"], [1])
            self.assertEqual(observation["instruction"]["text"], "long HA text")


if __name__ == "__main__":
    unittest.main()
