from Corrector import Corrector
from Selector import Selector
import logging
import sys
import os
import json
import codecs
from datetime import datetime
import random
current_time = datetime.now()
current_time_str = current_time.strftime("%Y%m%d-%H%M")
logging.basicConfig(filename=f"./log/{current_time_str}_main.log", level=logging.INFO)
logger = logging.getLogger()

def main(continue_question_id, end_question_id, db_root_path, read_path, output_root_path, tables_path, shot_path = None, mode='base', MAX_NUMS=3, shot_nums = 3):

    decoder = Decoder()
    corrector = Corrector(db_root_path)
    
    if shot_path:
        with open(shot_path, 'r', encoding='utf8') as f:
            shot_examples = json.load(f)
    
    # save path
    prompt_save_path = os.path.join(output_root_path, "input-" + continue_question_id +".txt")
    sql_save_path = os.path.join(output_root_path, "sql-" + continue_question_id +".txt")
    corre_prompt_save_path = os.path.join(output_root_path, "corre_input-" + continue_question_id +".txt")
    corre_sql_save_path = os.path.join(output_root_path, "corre_sql-" + continue_question_id +".txt")


    selected_data = json.load(open(read_path, 'r', encoding='utf-8'))
    n_data = len(selected_data)
    assert 0 <= int(continue_question_id) < n_data, "The starting point is invalid; it should range from 0 to the maximum sample index value {n_data-1}."
    logger.info(f"continue to output, begin question_id ={continue_question_id}, all question nums is: {n_data}")

    with codecs.open(prompt_save_path, 'a+', encoding='utf8') as fout_prompt, \
        codecs.open(sql_save_path, 'a+', encoding='utf8') as fout_sql, \
        codecs.open(corre_prompt_save_path, 'a+', encoding='utf8') as fout_corre_prompt, \
        codecs.open(corre_sql_save_path, 'a+', encoding='utf8') as fout_corrt:
        for i in range(n_data):
            print('processing gpt4 {}/{} ({:.2f}%%)\r'.format(i, n_data, 100 * i / n_data), end='')
            data = selected_data[i]
            real_question_id = data.get("question_id", i)

            if int(end_question_id) > real_question_id >= int(continue_question_id):
                logger.info(f"Begin question_id ={continue_question_id}, current question_id ={real_question_id}")
                db_id = data['db_id']
                query = data['question']
                evidence = data.get('evidence','')


                # Column selection: Directly load preset results
                schema = data['desc_str']
                fk = data['fk_str']
                origin_schema = data['full_origin_schema']

                # Main method SQL generation
                if mode == 'skeleton':
                    shot_ids = data['shot_list']
                    shot_prompts = [shot_examples[str(i)] for i in shot_ids]
                    prompt, reply, cleaned_sql = decoder.skeleton_generate(query, evidence, schema, fk, shot_prompts, shot_nums)
                else:
                    prompt, reply, cleaned_sql = decoder.generate(query, evidence, schema, fk)                

                
                    
                info = f"*******question_id {str(real_question_id)}: {query}\n{prompt}{reply}\n*******\n\n"
                fout_prompt.write(info)
                fout_prompt.flush()
                info = f"{str(real_question_id)} question_id:{cleaned_sql}\n"
                fout_sql.write(info)
                fout_sql.flush()

                # Error Correction
                exec_result = corrector.execute_model(db_id, cleaned_sql, topn=5)
                # First step error correction: eliminate large model random errors
                step1_corre = 0
                while step1_corre < MAX_NUMS:
                    data = exec_result.get('data', None)
                    if data is not None and len(data) == 0:
                        if (step1_corre+1) >= MAX_NUMS*0.8:
                            shot_prompts = random.sample(shot_prompts, 3)
                        if mode == 'skeleton':
                            shot_ids = data['shot_list']
                            shot_prompts = [shot_examples[str(i)] for i in shot_ids]
                            prompt, reply, cleaned_sql = decoder.skeleton_generate(query, evidence, schema, fk, shot_prompts, shot_nums)
                        else:
                            prompt, reply, cleaned_sql = decoder.generate(query, evidence, schema, fk)  
                        exec_result = corrector.execute_model(db_id, cleaned_sql, topn=5)
                        step1_corre += 1
                    else:
                        break
                    
                # Step two error correction: Determine whether to perform step two error correction based on the results of step one correction
                data = exec_result.get('data', None)
                if data is not None and len(data) != 0 and step1_corre != 0:
                    corre_prompt, corre_reply, corr_sql =  prompt, '【correct SQL】【First step correction nums】' + str(step1_corre) + reply, cleaned_sql
                else:
                    corre_prompt, corre_reply, corr_sql = corrector.correction(db_id, cleaned_sql, query, evidence, schema, origin_schema, fk, MAX_NUMS=MAX_NUMS)

                
                info = f"*******question_id {str(real_question_id)}: {query}\n{corre_prompt}{corre_reply}\n*******\n\n"
                fout_corre_prompt.write(info)
                fout_corre_prompt.flush()
                info = f"{str(real_question_id)} question_id:{corr_sql}\n"
                fout_corrt.write(info)
                fout_corrt.flush()
            else:
                #Skip processed data
                logger.info(f"Skip processed data, question_id ={real_question_id}")
if __name__ == '__main__':

    continue_question_id = sys.argv[1]
    end_question_id = sys.argv[2]


    db_root_path = './data/spider/test_database'
    read_path = "./data/spider/test_data/test_0610.json"
    output_root_path = "./data/gpt4-output"
    train_shot_prompt = './data/spider/train/train_examples_prompt.json'
    tables_path = './data/spider/test_data/tables_test.json'


    mode = 'skeleton'
    MAX_NUMS = 2
    shot_nums = 2
    
    if not os.path.exists(output_root_path):
        try:
            os.makedirs(output_root_path)
            print(f"Directory created successfully: {output_root_path}")
        except OSError as e:
            print(f"Failed to create directory: {output_root_path}")        
    main(continue_question_id, end_question_id, db_root_path, read_path, output_root_path, tables_path, train_shot_prompt, mode, MAX_NUMS, shot_nums)





    