from .handlers import HandlerDescription
from .handlers.llm import OpenAIHandler
from .extensions import NewelleExtension


class NvidiaNIMExtension(NewelleExtension):
    name = "Nvidia NIM"
    id = "nvidianim"

    def get_llm_handlers(self) -> list:
        return [
            HandlerDescription("nvidianim", "Nvidia NIM", "Nvidia NIM API", NvidiaNIMHandler)
        ]


class NvidiaNIMHandler(OpenAIHandler):
    key = "nvidianim"
    
    def __init__(self, settings, path):
        super().__init__(settings, path)
        self.set_setting("endpoint", "https://integrate.api.nvidia.com/v1/")

    def get_extra_settings(self) -> list:
        return self.build_extra_settings(
                "Nvidia", True, True, False, True, True, None, None, False, True, True, True)
