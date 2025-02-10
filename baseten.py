from .handlers import HandlerDescription
from .handlers.llm import OpenAIHandler
from .extensions import NewelleExtension


class BasetenExtension(NewelleExtension):
    name = "Baseten LLM"
    id = "basetenext"

    def get_llm_handlers(self) -> list:
        return [
            HandlerDescription("baseten", "Baseten", "Baseten API - fast model inference", BasetenHandler)
        ]


class BasetenHandler(OpenAIHandler):
    key = "baseten"

    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://inference.baseten.co/v1/")

    def get_extra_settings(self) -> list:
        return self.build_extra_settings(
                "Baseten", True, True, False, True, True, None, None, False, True, True, True)
