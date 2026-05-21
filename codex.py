import socket
import subprocess
import time
import urllib.request
import gettext

from .extensions import NewelleExtension
from .handlers.llm.openai_handler import OpenAIHandler
from .handlers import ExtraSettings, ErrorSeverity
from .utility.system import can_escape_sandbox, get_spawn_command


class CodexHandler(OpenAIHandler):
    """LLM Handler that connects to a local ChatMock server for OpenAI Codex access."""

    key = "codex"
    default_models = (("gpt5.5", "gpt-5.5"),)

    def __init__(self, settings, path):
        self.server_process = None
        self._selected_port = self._find_free_port()
        super().__init__(settings, path)
        self.set_setting("api", "t")

    @staticmethod
    def requires_sandbox_escape() -> bool:
        """ChatMock must run on the host system."""
        return True

    def get_setting(self, key: str, search_default=True, return_value=None):
        if key == "endpoint" and hasattr(self, "_selected_port"):
            return f"http://127.0.0.1:{self._selected_port}/v1"
        return super().get_setting(key, search_default, return_value)

    def _find_free_port(self) -> int:
        """Bind to a random free port and return its number."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def get_extra_settings(self) -> list:
        settings = [
            ExtraSettings.ButtonSetting(
                "login",
                _("ChatMock Login"),
                _("Run chatmock login to authenticate with your ChatGPT account"),
                self._run_login,
                label=_("Login"),
            ),
        ]
        settings += self.build_extra_settings("Codex", False, True, False, True, True, None, None, False, True, True, True, False, False, True)
        return settings

    def _run_login(self, button=None):
        """Run chatmock login in a terminal."""
        if not can_escape_sandbox():
            self.throw(
                _("Sandbox escape is required to run ChatMock login"),
                ErrorSeverity.WARNING,
            )
            return
        try:
            subprocess.Popen(
                get_spawn_command() + ["chatmock", "login"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception as e:
            self.throw(
                _("Error running chatmock login: ") + str(e),
                ErrorSeverity.WARNING,
            )

    def _is_server_running(self) -> bool:
        """Check if the ChatMock server is already running."""
        endpoint = self.get_setting("endpoint", False)
        health_url = endpoint.rstrip("/") + "/models"
        try:
            urllib.request.urlopen(health_url, timeout=2)
            return True
        except Exception:
            return False

    def _start_server(self):
        """Start the chatmock serve process in the background."""
        if self.server_process is not None or self._is_server_running():
            return
        if not can_escape_sandbox():
            self.throw(
                _("Sandbox escape is required to run ChatMock"),
                ErrorSeverity.WARNING,
            )
            return
        try:
            self.server_process = subprocess.Popen(
                get_spawn_command()
                + ["chatmock", "serve", "--port", str(self._selected_port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            self.get_models(True)
        except Exception as e:
            self.throw(
                _("Error starting chatmock server: ") + str(e),
                ErrorSeverity.WARNING,
            )

    def _stop_server(self):
        """Stop the chatmock server process."""
        if self.server_process is not None:
            try:
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()
                    self.server_process.wait()
            except Exception:
                pass
            finally:
                self.server_process = None

    def load_model(self, model):
        """Ensure the ChatMock server is running."""
        if not self._is_server_running():
            self._start_server()
            # Wait up to 30 seconds for the server to be ready
            start_time = time.time()
            while time.time() - start_time < 30:
                if self._is_server_running():
                    break
                time.sleep(0.5)
        return self._is_server_running()

    def destroy(self):
        """Stop the ChatMock server when the handler is destroyed."""
        self._stop_server()
        super().destroy()


class CodexExtension(NewelleExtension):
    """Extension that registers the Codex (ChatMock) LLM handler."""

    id = "codex"
    name = "Codex (ChatMock)"

    def get_llm_handlers(self) -> list[dict]:
        return [
            {
                "key": "codex",
                "title": _("Codex"),
                "description": _(
                    "Use OpenAI Codex via ChatMock local server"
                ),
                "class": CodexHandler,
            }
        ]
