from .handlers import HandlerDescription
from .handlers.llm import OpenAIHandler
from .extensions import NewelleExtension


class KiloExtension(NewelleExtension):
    name = "Kilo Code Gateway"
    id = "kilo"

    def get_llm_handlers(self) -> list:
        return [
            HandlerDescription("kilo", "Kilo Code Gateway", "Kilo Code Gateway - OpenAI compatible API", KiloHandler)
        ]


class KiloHandler(OpenAIHandler):
    key = "kilo"

    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://api.kilo.ai/api/gateway")

    def get_extra_settings(self) -> list:
        return self.build_extra_settings(
                "Kilo", True, True, False, True, True, None, None, False, True, True, True)