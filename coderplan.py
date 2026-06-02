from .handlers import HandlerDescription
from .handlers.llm import OpenAIHandler
from .extensions import NewelleExtension


class CoderPlanExtension(NewelleExtension):
    name = "CoderPlan LLM"
    id = "coderplanext"

    def get_llm_handlers(self) -> list:
        return [
            HandlerDescription("coderplan", "CoderPlan", "CoderPlan API - OpenAI-compatible LLM provider", CoderPlanHandler)
        ]


class CoderPlanHandler(OpenAIHandler):
    key = "coderplan"

    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://api.coderplan.ai/v1/")

    def get_extra_settings(self) -> list:
        return self.build_extra_settings(
                "CoderPlan", True, True, False, True, True, None, None, False, True, True, True)
