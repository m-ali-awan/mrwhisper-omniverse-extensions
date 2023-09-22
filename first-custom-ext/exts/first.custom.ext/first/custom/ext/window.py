import omni.ui as ui
import omni.usd
import carb
import asyncio
import omni.kit.commands
from omni.kit.window.popup_dialog.form_dialog import FormDialog


class GenAIWindow(ui.Window):

    def __init__(self, title : str, **kwargs) -> None:
        super().__init__(title, **kwargs)

        self.frame.set_build_fn(self._build_fn)

    def _build_fn(self):
        with self.frame:
            with ui.ScrollingFrame():
                with ui.VStack(style=)