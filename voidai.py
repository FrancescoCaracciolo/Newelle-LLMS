from .handlers import HandlerDescription
from .handlers.llm import OpenAIHandler
from .extensions import NewelleExtension


class VoidAIExtension(NewelleExtension):
    name = "VoidAI LLM"
    id = "voidaiext"

    def get_llm_handlers(self) -> list:
        return [
            HandlerDescription("voidai", "VoidAI", "voidai.app API", VoidAIHandler)
        ]


class VoidAIHandler(OpenAIHandler):
    key = "voidai"
    
    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://api.voidai.app/v1/")

    def get_extra_settings(self) -> list:
        return self.build_extra_settings(
                "VoidAI", True, True, False, True, True, None, None, False, True, True, True)
