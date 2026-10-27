#!/usr/bin/env python3
import unittest

import numpy as np

from roboworld2026.track2.simplevln_social_agent import SocialSimpleVLNAgent
from roboworld2026.track2.social_depth_guard import SafeAction


class FakeSimpleVLN:
    def __init__(self) -> None:
        self.pending_action_list = [1, 1]
        self.resets = 0

    def reset(self) -> None:
        self.resets += 1
        self.pending_action_list = []

    def act(self, observations, info, episode_id):
        if not self.pending_action_list:
            self.pending_action_list.extend([1, 1])
        return {"action": self.pending_action_list.pop(0)}


def open_depth() -> np.ndarray:
    return np.full((100, 100), 0.9, dtype=np.float32)


def blocked_depth() -> np.ndarray:
    depth = np.full((100, 100), 0.9, dtype=np.float32)
    depth[55:90, 40:60] = 0.03
    depth[55:90, 60:80] = 0.06
    return depth


class SocialSimpleVLNAgentTests(unittest.TestCase):
    def test_open_path_passes_base_forward(self) -> None:
        agent = SocialSimpleVLNAgent(FakeSimpleVLN())
        self.assertEqual(agent.act({"depth": open_depth()}, {}, "1"), {"action": 1})

    def test_blocked_path_preserves_base_forward_intent(self) -> None:
        base = FakeSimpleVLN()
        agent = SocialSimpleVLNAgent(base)
        first = agent.act({"depth": blocked_depth()}, {}, "1")
        self.assertEqual(first, {"action": 2})
        self.assertEqual(base.pending_action_list[0], 1)
        self.assertEqual(agent.actions[0], SafeAction.LEFT.value)


if __name__ == "__main__":
    unittest.main()
