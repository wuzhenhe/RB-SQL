import sys
import time
import json
from llm_config import  *
import random
from const_0521 import *

def request_random_engine(content, engine_name):
    response = openai.ChatCompletion.create(
        engine=engine_name,
        messages=[{"role": "user", "content": content}],
        temperature=0.1
    )
    text = response['choices'][0]['message']['content'].strip()
    prompt_token = response['usage']['prompt_tokens']
    response_token = response['usage']['completion_tokens']
    return text, prompt_token, response_token 

def request_llm(input_prompt, engine_name):
    for round in range(MAX_REQUEST):
        try:
            sys_response, prompt_token, response_token = request_random_engine(input_prompt, model)
            return sys_response
        except Exception as e:
            time.sleep(10)
            print(e)
    return ''
    

if __name__ == '__main__':

    prompt = "Hello word!"
    res = request_llm(prompt)
    print(res)
    