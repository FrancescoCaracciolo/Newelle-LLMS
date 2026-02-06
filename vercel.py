from .handlers import HandlerDescription
from .handlers.llm import OpenAIHandler
from .extensions import NewelleExtension


class Vercelextension(NewelleExtension):
    name = "Vercel LLM"
    id = "vercel"

    def get_llm_handlers(self) -> list:
        return [
            HandlerDescription("vercel", "Vercel AI Gateway", "Free 5$/month of credits", VercelHandler)
        ]


class VercelHandler(OpenAIHandler):
    key = "vercel"
    
    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://ai-gateway.vercel.sh/v1/")

    def get_extra_settings(self) -> list:
        return self.build_extra_settings(
                "Nvidia", True, True, False, True, True, None, None, False, True, True, True)
