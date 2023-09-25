import omni.ext
import omni.ui as ui
from pxr import Usd, UsdGeom, Gf
from pxr import Usd, Sdf
import omni.usd
import openai
import carb
import json
import omni.kit
import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from .widget import ProgressBar

api_key = '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'
root_path = 'C:/Users/ov-user/Documents/mrwhisper-omniverse-extensions'
asset_dict = {'coffee table, of brownish color, appleseed':
        "http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/ArchVis/Residential/Furniture/FurnitureSets/Appleseed/Appleseed_CoffeeTable.usd",
        'sci fi girl':
        "omniverse://localhost/Projects/mr-whisper-test1-prjct/Scifi_Girl_v.usdz"}

async def return_object_of_focus(selected_objects, prompt,api_key):
    messages = []
    sys_header = '''You will get list of objects from omniverseStage.
    Your goal would be to return only 1 out of those items,
    that is of FOCUS from user. You have to decide this, based
    on the input question.
    Like if query is, MOve table 2 meters right. You have to return the 
    TABLE item path from given list.\n
    JUST RETURN ONE OUT OF GIVEN OPTIONS, NO EXPLANATION ETC'''
    system_mes = {"role": "system", "content": sys_header}
    example_q = {'role':'user','content':f'''Move table 2 meters left, 
                 and possible options are:['/World/Plane',
                                           '/World/Daybed','/World/CoffeTable']'''}
    example_re = {'role':'assistant','content':'/World/CoffeTable'}
    prompt = f'''{prompt}, and possible options are:{selected_objects}'''
    query_message = {'role': 'user', 'content': prompt}
    messages.append(system_mes)
    messages.append(example_q)
    messages.append(example_re)
    messages.append(query_message)

    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.openai.com/v1/chat/completions', json={
            'model': 'gpt-3.5-turbo',
            'messages': messages,
            'temperature': 0
        }, headers = {"Authorization": "Bearer %s" % api_key}) as resp:
            gpt4_res = await resp.json()
    print(gpt4_res)
    result = gpt4_res["choices"][0]["message"]['content']
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
                self.progress = ProgressBar()
    def execute_move(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Loop is closed")
        except RuntimeError as ex:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.create_task(self._execute_move(self.progress))

    async def _execute_move(self,progress_widget):
        run_loop = asyncio.get_event_loop()
        progress_widget.show_bar(True)
        task = run_loop.create_task(progress_widget.play_anim_forever())

        ctx = omni.usd.get_context()
        stage = ctx.get_stage()
        selection = ctx.get_selection().get_selected_prim_paths()
        prompt = self._prompt_model.as_string

        # Use the existing event loop to run the coroutine
        object_of_focus = await return_object_of_focus(selection, prompt,api_key)
        selected_prim = stage.GetPrimAtPath(object_of_focus)
        task.cancel()
        await asyncio.sleep(1)
        progress_widget.show_bar(False)

        xform = UsdGeom.Xformable(selected_prim)
        translate_op = None
        for op in xform.GetOrderedXformOps():
            if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                translate_op = op
                break

        if translate_op:
            # Get the current translation
            current_translation = translate_op.Get()

            # Modify the translation based on the direction and distance
            parameters = {'direction': 'right', 'distance': 15}
            direction = parameters['direction']
            distance = parameters['distance']

            if direction == 'right':
                current_translation[0] += distance
            elif direction == 'left':
                current_translation[0] -= distance

            # Set the new translation
            translate_op.Set(current_translation)
        else:
            carb.log_error("Translate operation not found.")

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