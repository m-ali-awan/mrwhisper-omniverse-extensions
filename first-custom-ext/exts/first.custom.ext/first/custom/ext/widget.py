

import omni.ui as ui
from omni.ui import color as cl
import asyncio
import omni
import carb

class ProgressBar:
    def __init__(self):
        self.progress_bar_window = None
        self.left = None
        self.right = None
        self._build_fn()

    async def play_anim_forever(self):
        fraction = 0.0
        while True:
            fraction = (fraction + 0.01) % 1.0
            self.left.width = ui.Fraction(fraction)
            self.right.width = ui.Fraction(1.0-fraction)
            await omni.kit.app.get_app().next_update_async()

    def _build_fn(self):
        with ui.VStack():
            self.progress_bar_window = ui.HStack(height=0, visible=False)
            with self.progress_bar_window:
                ui.Label("Processing", width=0, style={"margin_width": 3})
                self.left = ui.Spacer(width=ui.Fraction(0.0))
                ui.Rectangle(width=50, style={"background_color": cl("#76b900")})
                self.right = ui.Spacer(width=ui.Fraction(1.0))

    def show_bar(self, to_show):
        self.progress_bar_window.visible = to_show