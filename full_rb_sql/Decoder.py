from const import *
from llm_request import *
from utils import *
class Decoder(object):
    def __init__(self):
        super().__init__()
        pass
    def generate(self, query, evidence, schema, fk):

        prompt = decompose_template.format(query=query, evidence=evidence, desc_str=schema, fk_str=fk)
        reply = request_llm(prompt)
        sql = select_final_sql(reply, "```")
        sql = clean_result(sql)
        return prompt, reply, sql
    def skeleton_generate(self, query, evidence, schema, fk, shot_prompts, shot_nums):

        if shot_nums == 0:
            prompt = zeroshot_template.format(query=query, evidence=evidence, desc_str=schema, fk_str=fk)
        else:
            query_prompt = origin_template.format(query=query, evidence=evidence, desc_str=schema, fk_str=fk)
            shot_prompts = shot_prompts[:shot_nums]
            prompt = "\n\n==========\n\n".join([base_prompt] + shot_prompts + [query_prompt])
        reply = request_llm(prompt)
        sql = select_final_sql(reply, "```")
        sql = clean_result(sql)
        return prompt, reply, sql


