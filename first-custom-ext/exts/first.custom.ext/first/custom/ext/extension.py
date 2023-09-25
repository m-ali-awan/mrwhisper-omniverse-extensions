import omni.ext
import omni.ui as ui
from pxr import Usd, UsdGeom, Gf
from pxr import Usd, Sdf
import omni.usd
import openai
import carb
import json
import omni.kit


root_path = 'C:/Users/ov-user/Documents/mrwhisper-omniverse-extensions'
asset_dict = {'coffee table, of brownish color, appleseed':
        "http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/ArchVis/Residential/Furniture/FurnitureSets/Appleseed/Appleseed_CoffeeTable.usd",
        'sci fi girl':
        "omniverse://localhost/Projects/mr-whisper-test1-prjct/Scifi_Girl_v.usdz"}


def return_object_of_focus(selected_objects, prompt):
        
        messages = []
        sys_header = '''You will get list of objects from omniverse Stage.
        Your goal would be to return only 1 out of those items,
        that is of FOCUS from user. You have to decide this, based
        on the input question.
        Like if query is, MOve table 2 meters right. You have to return the 
        TABLE item path from given list'''
        system_mes = {"role":"system","content":sys_header}
        prompt = f'''{prompt}, and possible options are:{selected_objects}'''
        query_message  = {'role':'user','content':prompt}
        messages.append(system_mes)
        messages.append(query_message)    

        gpt4_res=openai.ChatCompletion.create(
                            #model="gpt-3.5-turbo",
                            #model = model_to_use,
                            messages=messages,
                            temperature=0
                                    )
        result = gpt4_res(gpt4_res['choices'][0].message.content)
        return result

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
                ui.Button("Move Asset", clicked_fn=self.execute_move)

    
    def execute_move(self):
        ctx = omni.usd.get_context()
        stage = ctx.get_stage()
        selection = ctx.get_selection().get_selected_prim_paths()
        prompt = self._prompt_model.as_string

        object_of_focus = return_object_of_focus(selection,prompt)
        selected_prim = stage.GetPrimAtPath(object_of_focus) 
    
    def _place_asset(self):
        ctx = omni.usd.get_context()
        stage = ctx.get_stage()
        selection = ctx.get_selection().get_selected_prim_paths()
        
        if len(selection) == 0:
            carb.log_warn("No object selected.")
            return

        selected_path = str(selection[5])
        selected_prim = stage.GetPrimAtPath(selected_path)
        asset_dict = {}
        for prim in stage.TraverseAll():
            prim_info={}
            if not prim.IsActive():
                    
                continue
                
                # Get the prim's type name (e.g., Xform, Mesh, etc.)
                type_name = prim.GetTypeName()
                prim_info['type'] = str(type_name)
                
                # Get the prim's translation (if available)
                xform_attr = prim.GetAttribute('xformOp:translate')
                if xform_attr and xform_attr.IsValid():
                    translation = xform_attr.Get()
                    if translation:
                        prim_info['translation'] = [translation[0], translation[1], translation[2]]
        
        asset_dict[str(prim.GetPath())] = prim_info
        with open(f'{root_path}/first-custom-ext/Nbs/prim_dict.json', 'w+') as f:
            json.dump(asset_dict, f, indent=4)
        # Add more attributes here as needed
        
        # Add this prim's info to the main dictionary
        asset_dict[str(prim.GetPath())] = prim_info


        if not selected_prim or not selected_prim.IsValid():
            carb.log_warn(f"No valid prim at path {selected_path}")
            return

        # Process the prompt (simplified for demonstration)
        prompt = self._prompt_model.as_string
        if "table" in prompt:
            asset_path = "http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/ArchVis/Residential/Furniture/FurnitureSets/Appleseed/Appleseed_CoffeeTable.usd"
        else:
            carb.log_warn("No matching asset found for the prompt.")
            return

        # Place the asset (simplified for demonstration)
        new_prim_path = Sdf.Path(selected_path + "/NewAsset")
        new_prim = stage.DefinePrim(new_prim_path)
        #new_prim.GetReferences().AddReference(asset_path)

        carb.log_info(f"Placed new asset at {new_prim_path}")
    

    def move_object(self,prim, parameters):
        # getting current translations
        xform  = UsdGeom.Xformable(prim)
        translation = xform.getXformOpOrderAttr().Get()

        direction = parameters['direction']
        distance = parameters['distance']

        if direction == 'right':
            translation[0] += distance
        elif direction =='left':
            translation[0] -= distance

        xform.AddTranslateOp().Set(value = Gf.Vec3d(*translation))