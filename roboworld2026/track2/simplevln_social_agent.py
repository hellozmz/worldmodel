"""Wrapper that adds camera-only collision avoidance to SimpleVLN.

The wrapper is intentionally independent of Habitat at import time so its logic
can be unit-tested in CPU-only environments. In the official HA-VLN runtime it
wraps an already-constructed SimpleVLN agent and never reads ground-truth human
state from observations, information, or the simulator.
"""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from .social_depth_guard import SafeAction, SocialDepthGuard, convert_action_id


ACTION_ID: Mapping[SafeAction, int] = {
    SafeAction.STOP: 0,
    SafeAction.FORWARD: 1,
    SafeAction.LEFT: 2,
    SafeAction.RIGHT: 3,
    # LOOK_UP/LOOK_DOWN do not have stable SimpleVLN IDs; they are valid
    # Track 2 actions and are returned by name to the HA-VLN task.
    SafeAction.WAIT_A: -1,
    SafeAction.WAIT_B: -1,
}


class SocialSimpleVLNAgent:
    def __init__(
        self,
        base_agent: Any,
        *,
        depth_key: str = "depth",
        guard: SocialDepthGuard | None = None,
    ) -> None:
        self.base_agent = base_agent
        self.depth_key = depth_key
        self.guard = guard or SocialDepthGuard()
        self.actions: list[str] = []

    def reset(self) -> None:
        getattr(self.base_agent, "reset", lambda: None)()
        self.guard.reset()
        self.actions.clear()

    @staticmethod
    def _base_action_id(action: Any) -> int:
        if isinstance(action, dict):
            action = action.get("action")
        if isinstance(action, str):
            reverse = {member.value: member for member in SafeAction}
            if action in reverse:
                return ACTION_ID[reverse[action]]
            raise ValueError(f"unknown base action: {action}")
        return int(action)

    def act(self, observations: Mapping[str, Any], info: Mapping[str, Any], episode_id: Any) -> dict[str, Any]:
        base_result = self.base_agent.act(observations, info, episode_id)
        base_id = self._base_action_id(base_result)
        desired = convert_action_id(base_id)
        depth = observations.get(self.depth_key)
        if depth is None:
            raise KeyError(f"observation is missing camera-only depth at {self.depth_key!r}")
        safe = self.guard.next_action(desired, np.asarray(depth))

        if safe is not desired and desired is not SafeAction.STOP:
            # SimpleVLN consumed one action from its internal pending queue.
            # Put it back so the navigation intent is preserved after waiting or
            # beginning a side-step. This does not use privileged state.
            pending = getattr(self.base_agent, "pending_action_list", None)
            if pending is not None:
                pending.insert(0, base_id)

        self.actions.append(safe.value)
        if safe in (SafeAction.WAIT_A, SafeAction.WAIT_B):
            return {"action": safe.value}
        return {"action": ACTION_ID[safe]}


__all__ = ["ACTION_ID", "SocialSimpleVLNAgent"]
