import csv
import json
from utils import *
import sqlite3
from Knowledge import Knowledge
import os
from tqdm import tqdm

def get_column_desc(knowledge, db_name, table_name, column_name):
    base_desc = db_name + "||" + table_name + "||" + column_name
    return base_desc
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


def make_data(knowledge, data_path, columns_path, database_path, save_root_path):
    all_data = json.load(open(data_path, 'r', encoding='utf8'))
    all_arugs = json.load(open(columns_path, 'r', encoding='utf8'))
    queries = {}
    columns = {}

    queries_data = []
    columns_data = []
    query_pos_neg = []

    # 构建col字典
    for db_name in tqdm(all_arugs.keys(),desc ='构建col字典'):
        db = all_arugs[db_name]
        for table_name in db.keys():
            table = db[table_name]
            for column_name in table.keys():
                desc = get_column_desc(knowledge, db_name, table_name, column_name)
                columns[desc] = len(columns)
                if columns[desc] == 1008:
                    print(repr(desc))
    columns_data = [[value, key] for key, value in columns.items()]
    with open(save_root_path + '/columns.train.tsv', 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerows(columns_data)
    # 构建query字典
    for i in tqdm(range(len(all_data)), desc= '样例处理'):
        db_id = all_data[i]['db_id']
        gold  = all_data[i]['column_names']
        question = all_data[i]['question'].rstrip().rstrip('.') + '. '
        evidence = all_data[i]['evidence'].replace('\n',' ')
        q = (question+evidence).replace('\n', '')
        queries_data.append([i, q])

        for table_name in gold.keys():
            gold_columns = gold[table_name]
            all_columns = get_columns(database_path, db_id, table_name)
            for g in gold_columns:
                g_desc = get_column_desc(knowledge, db_id, table_name, g)
                for a in all_columns:
                    if a not in gold_columns:
                        a_desc = get_column_desc(knowledge, db_id, table_name, a)
                        query_pos_neg.append(str([i, columns[g_desc], columns[a_desc]]).replace(' ',''))
    
    # queries_data= [[value, key] for key, value in queries.items()]
    
    with open(save_root_path + '/queries.train.tsv', 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerows(queries_data)

    with open(save_root_path + '/triples.train.tsv', 'w', encoding='utf-8', newline='') as file:
        for row in query_pos_neg:
            file.write(row + '\n')

if __name__ == '__main__':
    knowledge = Knowledge('./bird_dev/dev.json', './bird_dev/dev_tables.json','./bird_dev/dev_databases/dev_databases/','./dev_knowledge.json')
    '''make_data(
        knowledge=knowledge, 
        data_path='./data/train_gold_tables_columns_0112.json', 
        columns_path='./train_db_table_col_info.json', 
        database_path='./data/train_databases', 
        save_root_path='./data')'''
    
    with open("./bird_dev/dev_part.json",'r', encoding="utf-8") as f:
        content = json.load(f)
        for i in range(len(content)):
            tables = list(content[i]["retrieval_tables"].keys())
            db_name = content[i]["db_id"]
            column_dic = {}
            for j in range(len(tables)):
                table = tables[j]
                column_names = get_columns('./bird_dev/dev_databases/dev_databases', db_name, table)
                for k in range(len(column_names)):
                    column_names_desc = get_column_desc(knowledge, db_name, table, column_names[k])
                    print(column_names_desc)
