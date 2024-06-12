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


content = 0
with open("../spider/test.processed_20240306.json",'r', encoding="utf-8") as f:
    content = json.load(f)
dic = 0
with open("../spider/test_db2tables.json",'r', encoding="utf-8") as f:
    dic = json.load(f)

print(len(content))

random.seed(12345)

parser = Arguments(description='inference')

parser.add_model_parameters()
parser.add_model_inference_parameters()

parser.add_argument('--depth', dest='depth', required=False, default=None, type=int)

args = parser.parse()

args.colbert, args.checkpoint = load_colbert(args)

inference = ModelInference(args.colbert, amp=args.amp)

all=0
keep=0
for i in range(len(content)):
    if i%100==0:
        print(i)
    db_id = content[i]["db_id"]
    question = content[i]["question"]
    #evidence = content[i]["evidence"]
    question = [(question).replace('\n', '')]
    tables = dic[db_id]
    sim_dic = {}
    name_list = []
    key_embeddings= []
    tables_content = []
    for j in range(len(tables)):
        name = tables[j]["table_name"]
        columns = tables[j]["content"]
        name_list.append(name)
        
        columns_array = "name:"+name+"||content:" 
        for k in range(len(columns)):
            columns_array = columns_array+columns[k]+"|"

        tables_content.append(columns_array)
        #query_embeddings = model.encode_queries(question_array, task=task)
        #key_embedding = model.encode_keys(columns, task=task)
        #key_embeddings.append(key_embedding)

        #similarity = query_embeddings @ key_embeddings.T

        #similarity = np.sum(np.max(np.array(similarity),axis=1))

        #sim_dic[name] = similarity
        #print(similarity)

    Q = inference.queryFromText(question)
    D = inference.docFromText(tables_content)
    #similarity_array = (-1.0 * ((Q.unsqueeze(2) - D.unsqueeze(1))**2).sum(-1)).max(-1).values.sum(-1)
    similarity_array = (Q @ D.permute(0, 2, 1)).max(2).values.sum(1)
    similarity_array = similarity_array.tolist()
    #print(similarity_array)
    
    for j in range(len(name_list)):
        sim_dic[name_list[j]] = similarity_array[j]

    sorted_sim_dic = sorted(sim_dic.items(),key=lambda x:x[1],reverse=True)
    record = 0
    sim_flag = sorted_sim_dic[0][1]
    for j in range(len(sorted_sim_dic)):
        if sorted_sim_dic[j][1]<6:
            record = j
            break
    if record>0:
        all = all+len(sorted_sim_dic)
        keep = keep+record
        sorted_sim_dic = sorted_sim_dic[:record]
    else:
        all = all+len(sorted_sim_dic)
        keep = keep+len(sorted_sim_dic)
    #print(sorted_sim_dic)
    #print(sim_flag)
    #print(record)
    #break
    if len(sorted_sim_dic)>5:
        sorted_sim_dic = dict(sorted_sim_dic)
    else:
        sorted_sim_dic = dict(sorted_sim_dic)
    content[i]["retrieval_tables"] = sorted_sim_dic
    #print(sorted_sim_dic)

print(float(keep)/float(all))

with open("../spider/test.processed_20240306_6.json",'w', encoding="utf-8") as f1:
    json.dump(content,f1,indent=4,ensure_ascii=False)



