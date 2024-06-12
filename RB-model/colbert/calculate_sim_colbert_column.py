import json
import numpy as np
import os
import random

from colbert.utils.parser import Arguments
from colbert.utils.runs import Run

from colbert.evaluation.loaders import load_colbert, load_topK, load_qrels
from colbert.evaluation.loaders import load_queries, load_topK_pids, load_collection
from colbert.evaluation.ranking import evaluate
from colbert.evaluation.metrics import evaluate_recall
from colbert.modeling.inference import ModelInference

import sys
import csv
import json
from utils import *
import sqlite3
from Knowledge import Knowledge
import os
from tqdm import tqdm

def get_column_desc(knowledge, db_name, table_name, column_name):
    base_desc = db_name + "||" + table_name + "||" + column_name
    #return base_desc
    try:
        cols_info = knowledge.knowledge[db_name]['tables'][table_name][column_name]
        full_column_name = cols_info['full_column_name']
        column_desc = cols_info['column_desc']
        examples = cols_info['examples']
        value_desc = cols_info['value_desc'].replace('\n',' ')
        all_select = []
        # 保证相似的信息只被添加一次
        column_desc = column_name if full_column_name == column_desc else column_desc
            
        if column_name != full_column_name:
            all_select.append(full_column_name)
        if column_name != column_desc:
            all_select.append(column_desc)
        if examples != '' and len(examples)<512:
             all_select.append(examples)
        if value_desc != '':
            all_select.append(value_desc)
        column_desc = ". ".join(all_select)
        return (base_desc + ": " + column_desc).replace('\n', ' ').replace('\r', ' ')

    except Exception as e:
        # print(str(e))
        return base_desc

def get_columns(databases_path, db_name, table_name):
    db_path = databases_path  + '/' + db_name + '/' + db_name + '.sqlite'
    assert os.path.exists(db_path), 'DB path is not found, the input path is: ' +  db_path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info('{}');".format(table_name))
    columns = cursor.fetchall()
    cols = []
    for column in columns:
        # column[1] 是名字：
        cols.append(column[1])
    if len(cols) == 0:
        print(table_name + " not find any cols")
    return cols




        

content = 0
with open("./bird_dev/dev.processed_1220_retrieval_3xcolbert_31.json",'r', encoding="utf-8") as f:
    content = json.load(f)


print(len(content))

random.seed(12345)

parser = Arguments(description='inference')

parser.add_model_parameters()
parser.add_model_inference_parameters()

parser.add_argument('--depth', dest='depth', required=False, default=None, type=int)

args = parser.parse()

args.colbert, args.checkpoint = load_colbert(args)

inference = ModelInference(args.colbert, amp=args.amp)


knowledge = Knowledge('./bird_dev/dev.json', './bird_dev/dev_tables.json','./bird_dev/dev_databases/dev_databases/','./dev_knowledge.json')


for i in range(len(content)):
    if i%100==0:
        print(i)
    tables = list(content[i]["retrieval_tables"].keys())
    db_name = content[i]["db_id"]
    question = (content[i]["question"]+content[i]["evidence"]).replace('\n','')
    question = [question]
    column_dic = {}
    for j in range(len(tables)):
        table = tables[j]
        column_names = get_columns('./bird_dev/dev_databases/dev_databases', db_name, table)
        column_names_desc = []
        for k in range(len(column_names)):
            temp = get_column_desc(knowledge, db_name, table, column_names[k])
            print(temp)
            column_names_desc.append(temp)
        sys.exit()
        Q = inference.queryFromText(question)
        D = inference.docFromText(column_names_desc)
        similarity_array = (Q @ D.permute(0, 2, 1)).max(2).values.sum(1)
        similarity_array = similarity_array.tolist()

        sim_dic = {}
        for k in range(len(column_names)):
            sim_dic[column_names[k]] = similarity_array[k]

        sorted_sim_dic = sorted(sim_dic.items(),key=lambda x:x[1],reverse=True)
        sorted_sim_dic = dict(sorted_sim_dic)
        content[i][table] = sorted_sim_dic



with open("./bird_dev/dev.processed_1220_retrieval_3xcolbert_31_column2.json",'w', encoding="utf-8") as f1:
    json.dump(content,f1,indent=4,ensure_ascii=False)



