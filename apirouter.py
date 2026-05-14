from .handlers import HandlerDescription
from .handlers.llm import OpenAIHandler
from .extensions import NewelleExtension


class ApiRouterExtension(NewelleExtension):
    name = "ApiRouter LLM"
    id = "apirouterext"

    def get_llm_handlers(self) -> list:
        return [
            HandlerDescription("apirouter", "ApiRouter", "ApiRouter - Free $0.50 credit", ApiRouterHandler)
        ]


class ApiRouterHandler(OpenAIHandler):
    key = "apirouter"

    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://apirouter.chat/v1/")

    def get_extra_settings(self) -> list:
        return self.build_extra_settings(
                "ApiRouter", True, True, False, True, True, None, None, False, True, True, True)
