import json
import threading
import time
import gettext
from typing import Any, Callable

import requests

from .extensions import NewelleExtension
from .handlers.llm.llm import LLMHandler
from .handlers import ExtraSettings
from .utility import get_streaming_extra_setting, convert_history_openai


AIHORDE_BASE_URL = "https://aihorde.net/api/v2"
AIHORDE_ANON_KEY = "0000000000"
POLL_INTERVAL = 2
MAX_POLL_TIME = 300

class AIHordeExtension(NewelleExtension):
    id = "aihorde"
    name = "AI Horde"

    def __init__(self, pip_path: str, extension_path: str, settings):
        super().__init__(pip_path, extension_path, settings)

    def get_llm_handlers(self) -> list[dict]:
        return [
            {
                "key": "aihorde",
                "title": _("AI Horde"),
                "description": _("Free, distributed AI text generation via AI Horde. Community-powered, supports anonymous access."),
                "class": AIHordeHandler,
            }
        ]


class AIHordeHandler(LLMHandler):
    key = "aihorde"
    default_models = (
        ("llama-3.1-8b", "llama-3.1-8b"),
    )

    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.models = self.default_models
        stored = self.get_setting("models", False)
        if stored is not None:
            try:
                self.models = json.loads(stored)
            except Exception:
                pass
        self._cached_kudos = None
        self._kudos_cache_time = 0
        threading.Thread(target=self._fetch_models, daemon=True).start()

    def _get_headers(self, extra=None):
        api_key = self.get_setting("api") or AIHORDE_ANON_KEY
        headers = {
            "apikey": api_key,
            "Client-Agent": "Newelle:1.0:https://github.com/qwersyk/Newelle",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    def _fetch_models(self):
        try:
            resp = requests.get(
                f"{AIHORDE_BASE_URL}/status/models?type=text",
                headers={"Client-Agent": "Newelle:1.0:https://github.com/qwersyk/Newelle"},
                timeout=15,
            )
            if resp.status_code == 200:
                models = resp.json()
                text_models = []
                for m in models:
                    name = m.get("name", "")
                    count = m.get("count", 0)
                    if count > 0:
                        text_models.append((name, f"{name} ({count} workers)"))
                if text_models:
                    self.models = tuple(text_models)
                    self.set_setting("models", json.dumps(self.models))
                    self.settings_update()
        except Exception:
            pass

    def get_models_list(self):
        return self.models

    def get_kudos(self):
        now = time.time()
        if self._cached_kudos is not None and now - self._kudos_cache_time < 60:
            return self._cached_kudos
        api_key = self.get_setting("api") or AIHORDE_ANON_KEY
        if api_key == AIHORDE_ANON_KEY:
            return None
        try:
            resp = requests.get(
                f"{AIHORDE_BASE_URL}/find_user",
                headers=self._get_headers(),
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                self._cached_kudos = data.get("kudos", 0)
                self._kudos_cache_time = now
                return self._cached_kudos
        except Exception:
            pass
        return None

    def refresh_models(self, button=None):
        self._fetch_models()

    def refresh_kudos(self, button=None):
        kudos = self.get_kudos()
        if kudos is not None:
            self.set_setting("kudos_display", f"Kudos: {kudos:.0f}")
            self.settings_update()

    @staticmethod
    def get_extra_requirements() -> list:
        return []

    def supports_vision(self) -> bool:
        return False

    def get_extra_settings(self) -> list:
        settings = [
            ExtraSettings.EntrySetting(
                "api", _("API Key"),
                _("AI Horde API key. Use 0000000000 for anonymous access (lower priority). "
                  "Register at aihorde.net for a key with higher priority."),
                AIHORDE_ANON_KEY, password=True,
                website="https://aihorde.net/register",
            ),
            ExtraSettings.ComboSetting(
                "model", _("Text Model"),
                _("AI Horde text generation model"),
                self.models,
                self.models[0][0] if self.models else "",
                refresh=lambda x: self.refresh_models(x),
                website="https://aihorde.net/api/",
            ),
            ExtraSettings.ScaleSetting(
                "max_context_length", _("Max Context Length"),
                _("Maximum context length in tokens for the generation"),
                2048, 256, 8192, 0,
            ),
            ExtraSettings.ScaleSetting(
                "max_length", _("Max Output Tokens"),
                _("Maximum number of tokens to generate"),
                256, 16, 1024, 0,
            ),
            ExtraSettings.ScaleSetting(
                "temperature", _("Temperature"),
                _("Sampling temperature. Higher values increase randomness"),
                0.7, 0.0, 2.0, 1,
            ),
            ExtraSettings.ScaleSetting(
                "top_p", _("Top-P"),
                _("Nucleus sampling threshold"),
                0.9, 0.0, 1.0, 2,
            ),
            ExtraSettings.ScaleSetting(
                "top_k", _("Top-K"),
                _("Top-K sampling threshold"),
                100, 0, 500, 0,
            ),
            ExtraSettings.ScaleSetting(
                "rep_pen", _("Repetition Penalty"),
                _("Penalty for repeated tokens"),
                1.1, 1.0, 2.0, 2,
            ),
            ExtraSettings.ToggleSetting(
                "trusted_workers", _("Trusted Workers Only"),
                _("Only send the request to trusted workers"),
                False,
            ),
            ExtraSettings.ToggleSetting(
                "slow_workers", _("Allow Slow Workers"),
                _("Allow slower workers to pick up the request"),
                True,
            ),
            ExtraSettings.ButtonSetting(
                "refresh_kudos", _("Check Kudos Balance"),
                _("Query your current kudos balance"),
                self.refresh_kudos, label=_("Check Kudos"),
            ),
            get_streaming_extra_setting(),
        ]
        return settings

    def _build_history_prompt(self, history: list, system_prompt: list) -> str:
        openai_msgs = convert_history_openai(history, system_prompt, False, False)
        parts = []
        for msg in openai_msgs:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"System: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")
            elif role == "tool":
                parts.append(f"Tool: {content}")
            else:
                parts.append(f"User: {content}")
        return "\n".join(parts)

    def _submit_text(self, prompt: str) -> dict:
        payload = {
            "prompt": prompt,
            "params": {
                "max_context_length": int(self.get_setting("max_context_length")),
                "max_length": int(self.get_setting("max_length")),
                "temperature": float(self.get_setting("temperature")),
                "top_p": float(self.get_setting("top_p")),
                "top_k": int(self.get_setting("top_k")),
                "rep_pen": float(self.get_setting("rep_pen")),
            },
            "models": [self.get_setting("model")],
            "trusted_workers": self.get_setting("trusted_workers"),
            "slow_workers": self.get_setting("slow_workers"),
        }
        resp = requests.post(
            f"{AIHORDE_BASE_URL}/generate/text/async",
            headers=self._get_headers(),
            json=payload,
            timeout=30,
        )
        if resp.status_code == 202:
            data = resp.json()
            return {"id": data["id"], "kudos": data.get("kudos", 0)}
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        msg = body.get("message", resp.text)
        raise Exception(f"AI Horde submission failed ({resp.status_code}): {msg}")

    def _poll_text_status(self, request_id: str) -> dict:
        resp = requests.get(
            f"{AIHORDE_BASE_URL}/generate/text/status/{request_id}",
            headers={"Client-Agent": "Newelle:1.0:https://github.com/qwersyk/Newelle"},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
        raise Exception(f"AI Horde status check failed ({resp.status_code})")

    def _cancel_text_request(self, request_id: str):
        try:
            requests.delete(
                f"{AIHORDE_BASE_URL}/generate/text/status/{request_id}",
                headers=self._get_headers(),
                timeout=10,
            )
        except Exception:
            pass

    def generate_text(self, prompt: str, history: list[dict[str, str]] = [], system_prompt: list[str] = []) -> str:
        if prompt.startswith("[Tool"):
            user = "Console"
        else:
            user = "User"
        history.append({"User": user, "Message": prompt})
        full_prompt = self._build_history_prompt(history, system_prompt)

        submit = self._submit_text(full_prompt)
        request_id = submit["id"]

        start = time.time()
        while time.time() - start < MAX_POLL_TIME:
            status = self._poll_text_status(request_id)
            if status.get("done", False):
                generations = status.get("generations", [])
                if generations and len(generations) > 0:
                    return generations[0].get("text", "").strip()
                raise Exception("AI Horde: generation completed but no text returned")
            if status.get("faulted", False):
                raise Exception("AI Horde: generation faulted")
            if not status.get("is_possible", True):
                raise Exception("AI Horde: no workers available for this model")
            time.sleep(POLL_INTERVAL)
        raise Exception("AI Horde: generation timed out")

    def generate_text_stream(self, prompt: str, history: list[dict[str, str]] = [], system_prompt: list[str] = [], on_update: Callable[[str], Any] = lambda _: None, extra_args: list = []) -> str:
        self.running = True

        if prompt.startswith("[Tool"):
            user = "Console"
        else:
            user = "User"
        history.append({"User": user, "Message": prompt})
        full_prompt = self._build_history_prompt(history, system_prompt)

        try:
            submit = self._submit_text(full_prompt)
        except Exception as e:
            self.running = False
            raise e
        request_id = submit["id"]
        kudos_cost = submit.get("kudos", 0)

        status_msg = f"Submitted to AI Horde (cost: {kudos_cost:.1f} kudos)..."
        args = (status_msg,) + tuple(extra_args)
        on_update(*args)

        start = time.time()
        prev_wait = -1
        prev_pos = -1
        try:
            while self.running and time.time() - start < MAX_POLL_TIME:
                try:
                    status = self._poll_text_status(request_id)
                except Exception:
                    time.sleep(POLL_INTERVAL)
                    continue

                if status.get("done", False):
                    generations = status.get("generations", [])
                    if generations and len(generations) > 0:
                        text = generations[0].get("text", "").strip()
                        args = (text,) + tuple(extra_args)
                        on_update(*args)
                        return text
                    self.running = False
                    raise Exception("AI Horde: generation completed but no text returned")

                if status.get("faulted", False):
                    self.running = False
                    raise Exception("AI Horde: generation faulted")

                if not status.get("is_possible", True):
                    self.running = False
                    raise Exception("AI Horde: no workers available for this model")

                wait = status.get("wait_time", 0)
                pos = status.get("queue_position", 0)
                processing = status.get("processing", 0)
                finished = status.get("finished", 0)

                if wait != prev_wait or pos != prev_pos:
                    if processing > 0:
                        status_msg = f"Generating... (finished: {finished}, wait: ~{wait}s)"
                    else:
                        status_msg = f"In queue: position {pos}, est. wait ~{wait}s"
                    args = (status_msg,) + tuple(extra_args)
                    on_update(*args)
                    prev_wait = wait
                    prev_pos = pos

                time.sleep(POLL_INTERVAL)

            if not self.running:
                self._cancel_text_request(request_id)
                return ""
            raise Exception("AI Horde: generation timed out")
        except Exception:
            self._cancel_text_request(request_id)
            raise
        finally:
            self.running = False

    def stop(self):
        self.running = False


