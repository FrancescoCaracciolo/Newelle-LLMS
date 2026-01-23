from .extensions import NewelleExtension
from .handlers import ExtraSettings, HandlerDescription 
from .handlers.llm import OpenAIHandler

class ZAIExtension(NewelleExtension):
    key = "zaillm"
    name="Z.AI LLM Provider"

    def get_llm_handlers(self) -> list[dict]:
        return [
            HandlerDescription("zai", "Z.AI", "Z.AI API", ZAIHandler) 
        ]

class ZAIHandler(OpenAIHandler):
    key="zai"
    default_models = (("glm-4.7", "glm-4.7"),)
    def __init__(self, settings, path):
        super().__init__(settings, path)
        if self.get_setting("zaiendpoint", False, "coding") == "coding":
            self.set_setting("endpoint", "https://api.z.ai/api/coding/paas/v4/")
        else:
            self.set_setting("endpoint", "https://api.z.ai/api/paas/v4/")

    def get_extra_settings(self) -> list:
        s = [
            ExtraSettings.ComboSetting("zaiendpoint", "Z.AI Endpoint", "Use coding endpoint if you are on the conding plan, otherwise use API", ["coding", "api"], "coding"),
        ]
        s += self.build_extra_settings("Z.AI", True, True, False, True, True, None, None, False, True, True, False)
        s += [
            ExtraSettings.ToggleSetting("enable_thinking", "Enable Thinking", "Choose if to enable thinking", True)
        ]
        return s

    def get_extra_body(self):
        body = super().get_extra_body()
        if not self.get_setting("enable_thinking"):
            body["thinking"] = {"type": "disabled"}
        return body 
