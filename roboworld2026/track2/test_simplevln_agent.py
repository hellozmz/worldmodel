#!/usr/bin/env python3
import unittest
from unittest.mock import patch

import numpy as np

from roboworld2026.track2.simplevln_agent import SimpleVLNHttpAgent


class SimpleVLNHttpAgentTests(unittest.TestCase):
    def make_agent(self, output: str) -> SimpleVLNHttpAgent:
        agent = SimpleVLNHttpAgent(
            base_urls=["http://server-a/v1", "http://server-b/v1"],
            model_name="simplevln",
        )
        patcher = patch.object(agent, "_post_chat", return_value=output)
        patcher.start()
        self.addCleanup(patcher.stop)
        return agent

    def obs(self):
        return {
            "rgb": np.zeros((8, 8, 3), dtype=np.uint8),
            "instruction": {"text": "Go to the door."},
        }

    def test_round_robin_and_first_action(self) -> None:
        agent = self.make_agent("forward 50 cm")
        self.assertEqual(agent.act(self.obs(), {}, "1"), {"action": 1})

    def test_action_chunk_is_limited_to_three_repeats(self) -> None:
        agent = self.make_agent("forward 150 cm, left 60 degrees")
        self.assertEqual(agent.act(self.obs(), {}, "1"), {"action": 1})
        self.assertEqual(agent.act(self.obs(), {}, "1"), {"action": 1})
        self.assertEqual(agent.act(self.obs(), {}, "1"), {"action": 1})
        self.assertEqual(agent.act(self.obs(), {}, "1"), {"action": 2})

    def test_invalid_output_uses_deterministic_fallback(self) -> None:
        agent = self.make_agent("unrecognized")
        first = agent.act(self.obs(), {}, "1")
        self.assertIn(first["action"], (1, 2, 3))


if __name__ == "__main__":
    unittest.main()
