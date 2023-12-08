#import openai
import aiohttp



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