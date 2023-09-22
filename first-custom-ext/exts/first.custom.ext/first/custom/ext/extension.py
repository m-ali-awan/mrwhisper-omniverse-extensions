
#Imports
import omni.ui as ui
import omni.usd
import carb
import asyncio
import omni.kit.commands

class MyExtension(omni.ext.IExt):

    def on_startup(self,ext_id):
        self._window = GenAIWindow("Do The Magic", width = 400, height = 525)
    
    def on_shutdown(self):
        self._window.destroy()
        self._window = None