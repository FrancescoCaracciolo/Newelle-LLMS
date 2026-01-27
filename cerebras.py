from .handlers import HandlerDescription
from .handlers.llm import OpenAIHandler
from .extensions import NewelleExtension


class CerebrasExtension(NewelleExtension):
    name = "Cerebras LLM"
    id = "cerebrasext"

    def get_llm_handlers(self) -> list:
        return [
            HandlerDescription("cerebras", "Cerebras", "Cerebras API - very fast LLM", CerebrasHandler)
        ]


class CerebrasHandler(OpenAIHandler):
    key = "cerebras"
    
    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://api.cerebras.ai/v1/")

    def get_extra_settings(self) -> list:
        return self.build_extra_settings(
                "Cerebras", True, True, False, True, True, None, None, False, True, True, True)
