import omni.ext
import omni.ui as ui
from pxr import Usd, UsdGeom, Gf
from pxr import Usd, Sdf
import omni.usd
import openai
import carb

dict = {'coffee table, of brownish color, appleseed':
        "http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/ArchVis/Residential/Furniture/FurnitureSets/Appleseed/Appleseed_CoffeeTable.usd",
        'sci fi girl':
        "omniverse://localhost/Projects/mr-whisper-test1-prjct/Scifi_Girl_v.usdz"}

class MyExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        self._prompt_model = ui.SimpleStringModel()
        self._window = ui.Window("Asset Placer", width=400, height=200)
        self._window.frame.set_build_fn(self._build_fn)
        #self._window.show()

    def on_shutdown(self):
        self._window.destroy()
        self._window = None

    def _build_fn(self):
        with self._window.frame:
            with ui.VStack():
                ui.Label("Enter your prompt:")
                ui.StringField(model=self._prompt_model)
                ui.Button("Place Asset", clicked_fn=self._place_asset)

    def _place_asset(self):
        ctx = omni.usd.get_context()
        stage = ctx.get_stage()
        selection = ctx.get_selection().get_selected_prim_paths()
        
        if len(selection) == 0:
            carb.log_warn("No object selected.")
            return

        selected_path = str(selection[0])
        selected_prim = stage.GetPrimAtPath(selected_path)

        if not selected_prim or not selected_prim.IsValid():
            carb.log_warn(f"No valid prim at path {selected_path}")
            return

        # Process the prompt (simplified for demonstration)
        prompt = self._prompt_model.as_string
        if "table" in prompt:
            asset_path = "/path/to/table_asset.usd"
        else:
            carb.log_warn("No matching asset found for the prompt.")
            return

        # Place the asset (simplified for demonstration)
        new_prim_path = Sdf.Path(selected_path + "/NewAsset")
        new_prim = stage.DefinePrim(new_prim_path)
        new_prim.GetReferences().AddReference(asset_path)

        carb.log_info(f"Placed new asset at {new_prim_path}")