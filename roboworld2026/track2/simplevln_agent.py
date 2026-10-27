"""Habitat-0.1.7-compatible SimpleVLN HTTP policy client.

Upstream SimpleVLN targets Habitat 0.3.3 and imports newer habitat-baselines
configuration modules. Track 2's official replay runtime is Habitat 0.1.7, so
this module preserves the public policy's prompt, history sampling, action-chunk
parser, and decoding parameters while depending only on Pillow and Python's
standard library.
"""

from __future__ import annotations

import base64
from io import BytesIO
import json
import random
import re
import time
from typing import Any, Mapping
import urllib.request

import numpy as np
from PIL import Image


SYSTEM_PROMPT = "You are a visual language navigation model."
PROMPT_TEMPLATE = (
    "Imagine you are a robot programmed for navigation tasks. "
    "You have been given a video of historical observations and an image of the "
    "current observation. Your assigned task is: '{}'. Analyze this series of "
    "images to decide your next move, which could involve turning left or right "
    "by a specific degree or moving forward a certain distance."
)


class SimpleVLNHttpAgent:
    """Action IDs follow Habitat's common mapping: 0 stop, 1 forward, 2 left, 3 right."""

    def __init__(
        self,
        *,
        base_urls: str | list[str],
        model_name: str,
        forward_distance_cm: float = 25.0,
        turn_angle_deg: float = 15.0,
        max_action_history: int = 200,
        resolution_ratio: float = 1.0,
        temperature: float = 0.3,
        top_p: float = 0.95,
        max_completion_tokens: int = 512,
        request_timeout_s: int = 600,
        max_history_images: int = 8,
        seed: int = 41,
    ) -> None:
        if isinstance(base_urls, str):
            urls = [item.strip() for item in base_urls.split(",") if item.strip()]
        else:
            urls = [item.strip().rstrip("/") for item in base_urls if item.strip()]
        if not urls or not all(item.endswith("/v1") for item in urls):
            raise ValueError("each SimpleVLM endpoint must end with /v1")
        if not 0 < resolution_ratio <= 1:
            raise ValueError("resolution_ratio must be in (0, 1]")
        self.urls = urls
        self.model_name = model_name
        self.forward_distance = float(forward_distance_cm)
        self.turn_angle = float(turn_angle_deg)
        self.max_action_history = int(max_action_history)
        self.resolution_ratio = float(resolution_ratio)
        self.temperature = temperature
        self.top_p = top_p
        self.max_completion_tokens = max_completion_tokens
        self.request_timeout_s = request_timeout_s
        self.max_history_images = max_history_images
        self.random = random.Random(seed)
        self._client_index = 0
        self.pending_action_list: list[int] = []
        self.rgb_list: list[Image.Image] = []
        self.reset()

    def reset(self) -> None:
        self.pending_action_list.clear()
        self.rgb_list.clear()

    @staticmethod
    def encode_image(image: Image.Image) -> str:
        stream = BytesIO()
        image.save(stream, format="JPEG", quality=90)
        return base64.b64encode(stream.getvalue()).decode("ascii")

    @staticmethod
    def uniform_sample_with_ends(values: list[Image.Image], count: int) -> list[Image.Image]:
        if len(values) <= count:
            return values
        indices = [round(index * (len(values) - 1) / (count - 1)) for index in range(count)]
        return [values[index] for index in indices]

    def _post_chat(self, payload: Mapping[str, Any]) -> str:
        url = self.urls[self._client_index % len(self.urls)] + "/chat/completions"
        self._client_index += 1
        data = json.dumps(payload, ensure_ascii=False).encode()
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        last_error = None
        for attempt in range(5):
            try:
                with urllib.request.urlopen(request, timeout=self.request_timeout_s) as response:
                    result = json.load(response)
                return result["choices"][0]["message"]["content"]
            except Exception as exc:  # vLLM endpoints are expected to recover transient failures
                last_error = exc
                if attempt == 4:
                    raise
                time.sleep(min(2**attempt, 15))
        raise RuntimeError(f"SimpleVLN request failed: {last_error}")

    def predict(self) -> str:
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": "Imagine you are a robot programmed for navigation tasks. "
                "You have been given a video of historical observations",
            }
        ]
        prior = self.rgb_list[:-1]
        if prior:
            for image in self.uniform_sample_with_ends(prior, self.max_history_images):
                content.append(self.image_content(image))
        else:
            content.append(self.image_content(self.rgb_list[-1]))
        content.extend(
            [
                {"type": "text", "text": "and an image of the current observation"},
                self.image_content(self.rgb_list[-1]),
                {"type": "text", "text": PROMPT_TEMPLATE.format(self.instruction).split("current observation.", 1)[1]},
            ]
        )
        output = self._post_chat(
            {
                "messages": [
                    {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
                    {"role": "user", "content": content},
                ],
                "model": self.model_name,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "max_completion_tokens": self.max_completion_tokens,
            }
        )
        output = re.sub(r"<think>.*?</think>", "", output, flags=re.DOTALL).strip()
        return output

    @classmethod
    def image_content(cls, image: Image.Image) -> dict[str, Any]:
        return {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{cls.encode_image(image)}"},
        }

    def extract_result(self, output: str) -> tuple[int | None, float | None]:
        match = re.search(r"<answer>(.*?)</answer>", output, flags=re.DOTALL)
        if match:
            output = match.group(1)
        output = output.strip().lower()
        if "stop" in output:
            return 0, None
        if "forward" in output:
            match = re.search(r"-?\d+(?:\.\d+)?", output)
            return 1, float(match.group()) if match else self.forward_distance
        if "left" in output:
            match = re.search(r"-?\d+(?:\.\d+)?", output)
            return 2, float(match.group()) if match else self.turn_angle
        if "right" in output:
            match = re.search(r"-?\d+(?:\.\d+)?", output)
            return 3, float(match.group()) if match else self.turn_angle
        return None, None

    def extract_multi_result(self, output: str) -> list[tuple[int | None, float | None]]:
        return [self.extract_result(item) for item in output.split(", ")]

    def act(self, observations: Mapping[str, Any], info: Mapping[str, Any], episode_id: Any) -> dict[str, int]:
        del info, episode_id
        if self.pending_action_list:
            return {"action": self.pending_action_list.pop(0)}
        rgb = np.asarray(observations["rgb"])
        if rgb.ndim != 3 or rgb.shape[2] not in (3, 4):
            raise ValueError(f"invalid RGB observation shape: {rgb.shape}")
        image = Image.fromarray(rgb[..., :3].astype("uint8"))
        if self.resolution_ratio < 1:
            image = image.resize((max(1, round(image.width * self.resolution_ratio)), max(1, round(image.height * self.resolution_ratio))))
        self.rgb_list.append(image)
        if len(self.rgb_list) > self.max_action_history:
            self.rgb_list.pop(0)
        self.instruction = str(observations["instruction"]["text"])

        parsed = self.extract_multi_result(self.predict())[:2]
        for action_index, numeric in parsed:
            if action_index == 0:
                self.pending_action_list.append(0)
            elif action_index == 1:
                count = max(1, min(3, round(float(numeric) / self.forward_distance)))
                self.pending_action_list.extend([1] * count)
            elif action_index in (2, 3):
                count = max(1, min(3, round(float(numeric) / self.turn_angle)))
                self.pending_action_list.extend([action_index] * count)
        if not self.pending_action_list:
            action = self.random.randint(1, 3)
            self.pending_action_list.append(action)
        return {"action": self.pending_action_list.pop(0)}


__all__ = ["SimpleVLNHttpAgent"]
