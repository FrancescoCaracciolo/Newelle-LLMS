from .extensions import NewelleExtension
from .handlers.llm import OpenAIHandler
from .handlers.extra_settings import ExtraSettings
from .handlers import HandlerDescription
import json
import time
from subprocess import check_output
from .utility.system import get_spawn_command
import os 

class QwenCodeExtension(NewelleExtension):
    id="qwencode"
    name="QwenCode LLM"
   
    def get_llm_handlers(self) -> list[dict]:
        return [HandlerDescription("qwen-code", "QwenCode", "QwenCode LLM", QwenCodeLLM)]


class QwenCodeLLM(OpenAIHandler):
    key="qwen-code"
    default_models = (("coder-model", "coder-model"), ("vision-model", "vision-model"))
    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://portal.qwen.ai/v1")

    def get_extra_settings(self) -> list:
        
        s = [
            ExtraSettings.ToggleSetting("get_api", "Get token from local qwen", "Automatically get token from existing installation of Qwen code", False),
        ]
        if not self.get_setting("get_api", False, False):
            s += [
                ExtraSettings.EntrySetting("api", "API Key", "The API key to use", "", password=True),
            ]
        else:
            s += [
                ExtraSettings.EntrySetting("qwen_path", "Qwen Token path", "The path where qwen code json file is stored", "~/.qwen/oauth_creds.json", password=False),
            ]
        s += self.build_extra_settings("Qwen Code", False, True, False, True, True, None, None, False, True, True, True)

        return s
    
    def get_token(self):
        check_output(get_spawn_command() + ["bash", "-c", "timeout 2 qwen"])

    def get_models(self, manual=False):
        self.set_api()
        return super().get_models(manual)
    
    def set_api(self):
        print("getting api")
        if self.get_setting("get_api"):
            path = os.path.expanduser(self.get_setting("qwen_path"))
            with open(path) as f:
                token = json.load(f)
                if token["expiry_date"] < int(time.time()):
                    self.get_token()
                else:
                    self.set_setting("api", token["access_token"])

    def generate_text(self, prompt: str, history: list[dict[str, str]], system_prompt: list[str] = []) -> str:
        self.set_api()
        return super().generate_text(prompt, history, system_prompt)
    
    def generate_text_stream(self, prompt: str, history: list[dict[str, str]], system_prompt: list[str] = [], on_update = lambda _: None, extra_args: list = []) -> str:
        return super().generate_text_stream(prompt, history, system_prompt, on_update, extra_args)
