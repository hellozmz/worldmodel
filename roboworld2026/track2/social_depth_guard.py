"""Camera-only social-navigation guard for HA-R2R Track 2.

The guard intentionally receives no simulator state, human annotation, GPS, or
metric information. It uses only the forward depth image to suppress unsafe
forward moves and construct a short side-step plan.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
import math
from typing import Mapping

import numpy as np


class SafeAction(str, Enum):
    STOP = "STOP"
    FORWARD = "MOVE_FORWARD"
    LEFT = "TURN_LEFT"
    RIGHT = "TURN_RIGHT"
    WAIT_A = "LOOK_UP"
    WAIT_B = "LOOK_DOWN"


@dataclass(frozen=True)
class DepthClearance:
    left_m: float
    center_m: float
    right_m: float
    left_free_fraction: float
    center_free_fraction: float
    right_free_fraction: float


class SocialDepthGuard:
    """Reactive, privacy-preserving obstacle guard for a forward RGB-D camera.

    The default thresholds are deliberately conservative for a 0.25 m forward
    step: a central object under 0.80 m blocks forward motion, while a candidate
    side corridor needs at least 1.05 m median clearance and 60% valid/far pixels.
    """

    def __init__(
        self,
        *,
        stop_distance_m: float = 0.80,
        side_distance_m: float = 1.05,
        max_depth_m: float = 10.0,
        normalized_depth: bool = True,
        detour_forwards: int = 3,
    ) -> None:
        if stop_distance_m <= 0 or side_distance_m < stop_distance_m:
            raise ValueError("depth thresholds must be positive and side clearance >= stop distance")
        if max_depth_m <= side_distance_m:
            raise ValueError("max depth must exceed side clearance")
        if detour_forwards < 1:
            raise ValueError("detour must contain at least one forward action")
        self.stop_distance_m = stop_distance_m
        self.side_distance_m = side_distance_m
        self.max_depth_m = max_depth_m
        self.normalized_depth = normalized_depth
        self.detour_forwards = detour_forwards
        self._plan: deque[SafeAction] = deque()
        self._wait_toggle = False

    def reset(self) -> None:
        self._plan.clear()
        self._wait_toggle = False

    def to_meters(self, depth: np.ndarray) -> np.ndarray:
        values = np.asarray(depth, dtype=np.float32)
        if values.ndim != 2:
            raise ValueError(f"depth must be 2-D, got shape {values.shape}")
        if self.normalized_depth:
            values = values * self.max_depth_m
        invalid = ~np.isfinite(values) | (values <= 0) | (values > self.max_depth_m)
        values[invalid] = np.nan
        return values

    @staticmethod
    def _region(values: np.ndarray, col_start: float, col_end: float, row_start: float, row_end: float) -> np.ndarray:
        height, width = values.shape
        rows = values[int(height * row_start):int(height * row_end), :]
        return rows[:, int(width * col_start):int(width * col_end)]

    @staticmethod
    def _median_and_free(values: np.ndarray, threshold_m: float) -> tuple[float, float]:
        if values.size == 0:
            return math.inf, 0.0
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            return math.inf, 0.0
        return float(np.median(finite)), float(np.mean(finite >= threshold_m))

    def clearance(self, depth: np.ndarray) -> DepthClearance:
        values = self.to_meters(depth)
        # A person's torso and legs normally occupy the lower two fifths of the
        # image. Ignore the sky/ceiling-heavy top and evaluate drivable space.
        regions = {
            name: self._region(values, *bounds)
            for name, bounds in {
                "left": (0.20, 0.40, 0.55, 0.90),
                "center": (0.40, 0.60, 0.55, 0.90),
                "right": (0.60, 0.80, 0.55, 0.90),
            }.items()
        }
        stats = {
            name: self._median_and_free(region, self.side_distance_m)
            for name, region in regions.items()
        }
        return DepthClearance(
            left_m=stats["left"][0],
            center_m=stats["center"][0],
            right_m=stats["right"][0],
            left_free_fraction=stats["left"][1],
            center_free_fraction=stats["center"][1],
            right_free_fraction=stats["right"][1],
        )

    def _side_is_clear(self, clearance: DepthClearance, side: str) -> bool:
        median = getattr(clearance, f"{side}_m")
        fraction = getattr(clearance, f"{side}_free_fraction")
        return median >= self.side_distance_m and fraction >= 0.60

    def next_action(self, desired: str | SafeAction, depth: np.ndarray) -> SafeAction:
        desired_action = SafeAction(desired)
        if desired_action is SafeAction.STOP:
            self.reset()
            return desired_action

        if self._plan:
            planned = self._plan.popleft()
            if planned is not SafeAction.FORWARD:
                return planned
            # Re-check before every planned side-step forward. If it is blocked,
            # abandon the old plan and let the normal reaction below choose again.
            self._plan.clear()

        if desired_action is not SafeAction.FORWARD:
            return desired_action

        clearance = self.clearance(depth)
        center_blocked = (
            clearance.center_m < self.stop_distance_m
            or clearance.center_free_fraction < 0.35
        )
        if not center_blocked:
            return SafeAction.FORWARD

        left_clear = self._side_is_clear(clearance, "left")
        right_clear = self._side_is_clear(clearance, "right")
        if left_clear or right_clear:
            if left_clear and right_clear:
                # Prefer the side with greater median clearance; tie-break on the
                # fraction of far pixels, then right for deterministic behavior.
                side = "left" if (
                    clearance.left_m,
                    clearance.left_free_fraction,
                ) > (
                    clearance.right_m,
                    clearance.right_free_fraction,
                ) else "right"
            else:
                side = "left" if left_clear else "right"
            opposite = SafeAction.RIGHT if side == "left" else SafeAction.LEFT
            turn = SafeAction.LEFT if side == "left" else SafeAction.RIGHT
            self._plan.extend([turn, turn])
            self._plan.extend([SafeAction.FORWARD] * self.detour_forwards)
            self._plan.extend([opposite, opposite])
            return self._plan.popleft()

        # No detected side corridor: wait without advancing the human animation.
        self._wait_toggle = not self._wait_toggle
        return SafeAction.WAIT_A if self._wait_toggle else SafeAction.WAIT_B


def convert_action_id(action_id: int) -> SafeAction:
    mapping: Mapping[int, SafeAction] = {
        0: SafeAction.STOP,
        1: SafeAction.FORWARD,
        2: SafeAction.LEFT,
        3: SafeAction.RIGHT,
    }
    try:
        return mapping[action_id]
    except KeyError as exc:
        raise ValueError(f"unknown Habitat action id: {action_id}") from exc


__all__ = ["DepthClearance", "SafeAction", "SocialDepthGuard", "convert_action_id"]
