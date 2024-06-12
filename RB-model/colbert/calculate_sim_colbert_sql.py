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


content_train = 0
with open("./bird_train/train.processed_1128_all_skeleton.json",'r', encoding="utf-8") as f:
    content_train = json.load(f)

content_dev = 0
with open("./bird_dev/dev.processed_1220.json",'r', encoding="utf-8") as f:
    content_dev = json.load(f)

questions_train = []
sqls_train = []
for i in range(len(content_train)):
    questions_train.append(content_train[i]["question_id"])
    sqls_train.append(content_train[i]["sql_skeleton"])


random.seed(12345)

parser = Arguments(description='inference')

parser.add_model_parameters()
parser.add_model_inference_parameters()

parser.add_argument('--depth', dest='depth', required=False, default=None, type=int)

args = parser.parse()

args.colbert, args.checkpoint = load_colbert(args)

inference = ModelInference(args.colbert, amp=args.amp)


for i in range(len(content_dev)):
    if i%100==0:
        print(i)
    question = content_dev[i]["question"]
    question = [question]
    similarity_array_all=[]
    Q = inference.queryFromText(question)
    for j in range((int)(len(sqls_train)/100)+1):
        if j==len(sqls_train)/100:
            sqls_train_temp = sqls_train[j*100:]
        else:
            sqls_train_temp = sqls_train[j*100:(j+1)*100]
        D = inference.docFromText(sqls_train_temp)
        similarity_array = (Q @ D.permute(0, 2, 1)).max(2).values.sum(1)
        similarity_array = similarity_array.tolist()
        similarity_array_all = similarity_array_all + similarity_array
    #print(similarity_array)
    
    sim_dic = {}


    for j in range(len(questions_train)):
        sim_dic[questions_train[j]] = similarity_array_all[j]

    sorted_sim_dic = sorted(sim_dic.items(),key=lambda x:x[1],reverse=True)
    
    #print(sorted_sim_dic)
    #print(sim_flag)
    #print(record)
    #break
    sorted_sim_dic = dict(sorted_sim_dic[:7])
    sorted_sim_arr = list(sorted_sim_dic.keys())
    content_dev[i]["few_shot_id_list"] = sorted_sim_arr
    #print(sorted_sim_dic)



with open("./bird_dev/dev.processed_1220_retrieval_colbert_all_sql_skeleton.json",'w', encoding="utf-8") as f1:
    json.dump(content_dev,f1,indent=4,ensure_ascii=False)



