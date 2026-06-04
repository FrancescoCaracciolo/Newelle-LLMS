from .handlers import HandlerDescription
from .handlers.llm import OpenAIHandler
from .extensions import NewelleExtension


class CommandCodeExtension(NewelleExtension):
    name = "Command Code LLM"
    id = "commandcodeext"

    def get_llm_handlers(self) -> list:
        return [
            HandlerDescription("commandcode", "Command Code", "Command Code API - OpenAI-compatible LLM provider", CommandCodeHandler)
        ]


class CommandCodeHandler(OpenAIHandler):
    key = "commandcode"

    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://api.commandcode.ai/provider/v1/")

    def get_extra_settings(self) -> list:
        return self.build_extra_settings(
                "Command Code", True, True, False, True, True, None, None, False, True, True, True)
