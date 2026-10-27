#!/usr/bin/env python3
import unittest

import numpy as np

from roboworld2026.track2.social_depth_guard import SafeAction, SocialDepthGuard


def depth_image(left_m: float, center_m: float, right_m: float) -> np.ndarray:
    depth = np.full((100, 100), 10.0, dtype=np.float32) / 10.0
    depth[55:90, 20:40] = left_m / 10.0
    depth[55:90, 40:60] = center_m / 10.0
    depth[55:90, 60:80] = right_m / 10.0
    return depth


class SocialDepthGuardTests(unittest.TestCase):
    def test_open_center_allows_forward(self) -> None:
        guard = SocialDepthGuard()
        action = guard.next_action(SafeAction.FORWARD, depth_image(5, 5, 5))
        self.assertEqual(action, SafeAction.FORWARD)

    def test_near_center_selects_clear_left_side(self) -> None:
        guard = SocialDepthGuard()
        action = guard.next_action(SafeAction.FORWARD, depth_image(5, 0.3, 0.7))
        self.assertEqual(action, SafeAction.LEFT)
        self.assertEqual(guard.next_action(SafeAction.FORWARD, depth_image(5, 0.3, 0.7)), SafeAction.LEFT)
        # The camera now points into the previously clear side corridor.
        self.assertEqual(guard.next_action(SafeAction.FORWARD, depth_image(5, 5, 5)), SafeAction.FORWARD)

    def test_blocked_corridor_waits_without_forward(self) -> None:
        guard = SocialDepthGuard()
        first = guard.next_action(SafeAction.FORWARD, depth_image(0.5, 0.3, 0.6))
        second = guard.next_action(SafeAction.FORWARD, depth_image(0.5, 0.3, 0.6))
        self.assertEqual({first, second}, {SafeAction.WAIT_A, SafeAction.WAIT_B})

    def test_stop_is_never_delayed(self) -> None:
        guard = SocialDepthGuard()
        self.assertEqual(guard.next_action(SafeAction.STOP, depth_image(0.1, 0.1, 0.1)), SafeAction.STOP)


if __name__ == "__main__":
    unittest.main()
