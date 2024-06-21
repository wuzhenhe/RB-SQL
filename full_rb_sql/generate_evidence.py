from Decoder import Decoder
from Corrector import Corrector
import logging
import sys
import os
import json
import codecs
from datetime import datetime
from const_0521 import *
from llm_request import *
from utils import *
current_time = datetime.now()
current_time_str = current_time.strftime("%Y%m%d-%H%M")
logging.basicConfig(filename=f"./log/{current_time_str}_main.log", level=logging.INFO)
logger = logging.getLogger()

if __name__ == '__main__':

    continue_question_id = sys.argv[1]
    end_question_id = sys.argv[2]

    read_path = "dev_process.json"
    output_root_path = "./data/bird/evidence"

    prompt_save_path = os.path.join(output_root_path, "input-" + continue_question_id +".txt")
    sql_save_path = os.path.join(output_root_path, "sql-" + continue_question_id +".txt")

    selected_data = json.load(open(read_path, 'r', encoding='utf-8'))

    n_data = len(selected_data)
    assert 0 <= int(continue_question_id) < n_data, "The starting point is invalid; it should range from 0 to the maximum sample index value {n_data-1}."
    logger.info(f"continue to output, begin question_id ={continue_question_id}, all question nums is: {n_data}")

    with codecs.open(prompt_save_path, 'a+', encoding='utf8') as fout_prompt, \
        codecs.open(sql_save_path, 'a+', encoding='utf8') as fout_sql:
        for i in range(n_data):
            print('processing gpt4 {}/{} ({:.2f}%%)\r'.format(i, n_data, 100 * i / n_data), end='')
            data = selected_data[i]
            real_question_id = data.get("question_id", i)

            if int(end_question_id) > real_question_id >= int(continue_question_id):
                logger.info(f"Begin question_id ={continue_question_id}, current question_id ={real_question_id}")
                db_id = data['db_id']
                query = data['question']
                evidence = data['evidence']

                schema_list = list(data['pre_knowledge_schema'].values())
                schema = "\n".join(schema_list)
                fk = data['full_knowledge_fk']

                prompt = evidence_prompt.format(desc_str=schema, fk_str=fk, query=query)

                reply = request_llm(prompt)
                info = f"*******question_id {str(real_question_id)}: {query}\n{prompt}{reply}\n*******\n\n"
                fout_prompt.write(info)
                fout_prompt.flush()
                evidence = evidence.replace("\n"," ")
                reply = reply.replace("\n"," ")
                info = f"question_id: {str(real_question_id)}\nOrigin evidence  : {evidence}\nPredict evidence : {reply}\n"
                fout_sql.write(info)
                fout_sql.flush()

            else:
                #Skip processed data
                logger.info(f"Skip processed data, question_id ={real_question_id}")
    