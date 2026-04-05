from typing import Any
from .handlers.descriptors import HandlerDescription
from .extensions import NewelleExtension
from .handlers.llm import OpenAIHandler
from .handlers import ExtraSettings
import requests
import json 


class CloudflareWorkersExtension(NewelleExtension):
    id = "cfworkers"
    name = "Cloudflare Workers LLM"

    def get_llm_handlers(self) -> list[dict]:
        return [
                HandlerDescription(
                    "cloudflare",
                    "Cloudflare AI Workers",
                    "Cloudflare AI workers LLM. Free 10'000 neurons/day",
                    CloudflareLLM
                    )
                ]


class CloudflareLLM(OpenAIHandler):
    key = "cloudflare"
    default_models = (("gemma-4-26b-a4b-it", "@cf/google/gemma-4-26b-a4b-it"),)
    
    def fetch_cloudflare_models(self):
        account_id = self.get_setting("account_id", False, None)
        api = self.get_setting("api", False, "")
        if account_id is None:
            return None
        r = requests.get(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/models/search?search=Text+Generation",
            headers={
                "Authorization": f'Bearer {api}',
                "Content-Type": "application/json",
            },
        )
        r.raise_for_status()
        models = r.json()["result"]
        ret_models = tuple()
        for model in models:
            ret_models += ((model["name"].split("/")[-1], model["name"]),)
        return ret_models

    def get_models(self, manual=False):
        if self.is_installed():
            try:
                import openai
                api = self.get_setting("api", False)
                cf_account = self.get_setting("account_id", False)
                if api is None or cf_account is None:
                    return
                result = self.fetch_cloudflare_models()
                self.models = result
                self.set_setting("models", json.dumps(result))
                self.settings_update()
            except Exception as e:
                if manual:
                    self.throw("Error getting " + self.key + " models: " + str(e), ErrorSeverity.WARNING)
                print("Error getting " + self.key + " models: " + str(e))
    
    def get_extra_settings(self) -> list:
        r = [
            ExtraSettings.EntrySetting("account_id", "Account ID", "Your Cloudflare Account ID, REQUIRED", "")
        ]
        r += self.build_extra_settings("CloudFlare", True, True, False, True, True, None, None, False, True, True, False)
        return r

    def get_setting(self, key: str, search_default=True, return_value=None) -> Any:
        if key == "endpoint":
            return "https://api.cloudflare.com/client/v4/accounts/"+self.get_setting("account_id", False, "")+"/ai/v1"
        return super().get_setting(key, search_default, return_value)
