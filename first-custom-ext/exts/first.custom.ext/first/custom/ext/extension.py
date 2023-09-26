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
from .tagged_assets import *
import ast
from .utils import format_string
#from .openai_related import return_object_of_focus


# Variables
api_key = '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'
root_path = 'C:/Users/ov-user/Documents/mrwhisper-omniverse-extensions'

async def test_parse_prompt(prompt):
    # Use ChatGPT to parse the prompt and extract necessary information
    # For simplicity, this function returns hardcoded values in this example
    return {
        "object_to_place": "omniverse://localhost/Projects/mr-whisper-test1-prjct/Scifi_Girl_v.usdz",
        "reference_object": "/World/Daybed",
        "relative_position": {"direction": "left", "distance": 2}
    }

async def return_object_of_focus(selected_objects, prompt,api_key):
    messages = []
    sys_header = '''You will get list of objects from omniverseStage.
    Your goal would be to return only 1 out of those items,
    that is of FOCUS from user,the DIRECTION to move in, and units to move. You have to decide this, based
    on the input question.
    Like if query is, Move table 2 meters right. You have to return the 
    TABLE item path from given list,DIRECTION.\n
    JUST RETURN ONE OUT OF GIVEN OPTIONS, NO EXPLANATION ETC'''
    system_mes = {"role": "system", "content": sys_header}
    example_q = {'role':'user','content':f'''Move table 2 meters left, 
                 and possible options are:['/World/Plane',
                                           '/World/Daybed','/World/CoffeTable']'''}
    example_re = {'role':'assistant','content':'/World/CoffeTable, Left, 2'}
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

async def return_new_object_and_position(asset_dict,current_objects,prompt,api_key):
   
    new_objects = list(asset_dict.keys())
    messages = []
    sys_header = ''' You have to return only a dict-type response. With following keys:
    - new_object
    - refernece_object,
    - new_object_direction
    - new_object_steps
    You will be provided with the paths of current objects in omniverse stage, and a list of tags 
    for to choose from new objects. You will return reference-object, what new object should be used, and in which direction
    and how many steps from refernece-object it should be placed. 
    DON'T GIVE ANY EXPLANATORY INFO, JUST THE REQUIRED KEYS\n
    *Again, keep in mind, return only in form of dict, as that has to be loaded as dict, 
    with mentioned keys.*'''
    system_mes = {"role": "system", "content": sys_header}
    example_q = {'role':'user','content':f'''Place a classic chair, 2 meters left of bed. \n 
                 and possible new-object options are:['coffee table, of brownish color, appleseed',
                                           'modern blue chair','old vantage chair'].\n
                 Objects present in current stage are:['/World/Plane',
                                           '/World/Daybed','/World/CoffeTable']'''}
    example_re = {'role':'assistant','content':'''{'new_object':'old vantage chair','reference_object':'/World/Daybed','new_object_direction':'left','new_object_steps':2}'''}
    prompt = f'''{prompt}, \n and possible new-object options are:{new_objects} \n
                Objects present in current stage are:{current_objects}'''
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
        self._window = ui.Window("Cognitive Scene Editing", width=400, height=200)
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
                #ui.Button("Place Asset", clicked_fn=self._place_asset)
                ui.Button('Test Place Asset', clicked_fn=self.test_place_asset)
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
        res = await return_object_of_focus(selection, prompt,api_key)
        object_of_focus,direct_gpt, steps_to_take  = res.split(',')
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
            parameters = {'direction': direct_gpt, 'distance': int(steps_to_take)}
            direction = parameters['direction']
            distance = parameters['distance']
            print(steps_to_take)
           
            to_check = direction.lower()
            if 'right' in to_check:
                print(f'SUCCESSFUL::{direction}')
                current_translation[0] += distance
            elif 'left' in to_check:
                print(f'SUCCESSFUL::{direction}')
                current_translation[0] -= distance
            else:
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
    


    def test_place_asset(self):#

        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError('Loop is Closed')
        except RuntimeError as ex:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.create_task(self._test_place_asset(progress_widget=self.progress))

    async def _test_place_asset(self,progress_widget):
        run_loop = asyncio.get_event_loop()
        progress_widget.show_bar(True)
        task = run_loop.create_task(progress_widget.play_anim_forever())

        ctx = omni.usd.get_context()
        stage = ctx.get_stage()
        selection = ctx.get_selection().get_selected_prim_paths()
        prompt = self._prompt_model.as_string
        #
        res = await return_new_object_and_position(asset_dict,
                                                   selection,prompt,api_key)
        res_dict = ast.literal_eval(res)
        print(f'Result Dict is::::{res_dict}')

        new_object_url= asset_dict[res_dict['new_object']]
        reference_object_pth = res_dict['reference_object']
        new_object_direction = res_dict['new_object_direction']   
        new_object_steps =res_dict['new_object_steps']                              

        new_name = format_string(res_dict['new_object'])

        reference_prim = stage.GetPrimAtPath(reference_object_pth)
        try:
            if reference_prim and reference_prim.isValid():
                xform = UsdGeom.Xformable(reference_prim)
                translate_op = None
                for op in xform.GetOrderedXformOps():
                    if op.GetOptype() == UsdGeom.XformOp.typeTranslate:
                        translate_op = op
                        break
                if translate_op:
                    translation = translate_op.Get()
                    print("Translation of the reference object:", translation)
                else:
                    print("Translate operation not found for the reference object.")
            else:
                print("Reference object not found.")

            new_translation_values = [translation[0] + 100,translation[1],translation[2]]
        except:
            new_translation_values = [0.0,0.0,0.0]
        omni.kit.commands.execute('CreatePayloadCommand',
                usd_context= omni.usd.get_context(),
                path_to=Sdf.Path(f'/World/{new_name}'),
                asset_path=new_object_url,
                instanceable=False)
        omni.kit.commands.execute('TransformMultiPrimsSRTCpp',
                count=1,
                paths=[f'/World/{new_name}'],
                #new_translations=[-156.4188672560385, 130.35249515180125, 199.61057602557773],
                new_translations = new_translation_values,
                new_rotation_eulers=[0.0, -90.0, -90.0],
                new_rotation_orders=[0, 1, 2],
                new_scales=[1.0, 1.0, 1.0],)
        
        


        task.cancel()
        await asyncio.sleep(1)
        progress_widget.show_bar(False)

