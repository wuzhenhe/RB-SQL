import os
import json
import sqlite3
import csv
from pprint import pprint
from utils_mac import *
from tqdm import tqdm
class Knowledge(object):
    def __init__(self, data_path: str, tables_json_path: str, databases_path: str, save_path: str):
        """
        :param data_path: dev/test.json
        :param tables_json_path: dev_tables.json/test_tables.json
        :param databases_path: database_description 
        :param save_path: save path
        """
        self.knowledge_json = self.select_column_full_names_and_fk(tables_json_path)
        # TODO !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self.save_knowledge(save_path.replace("knowledge","knowledge_json"), self.knowledge_json)
        if os.path.exists(save_path):
            self.load_knowledge(save_path)
        else:
            self.knowledge = self.generate_knowledge(data_path, tables_json_path, databases_path, save_path)
    def generate_knowledge(self, data_path, tables_json_path, databases_path, save_path):
        assert os.path.exists(data_path), 'Predict path is lost, please provide the correct file path like dev.json/test.json'
        assert os.path.exists(tables_json_path), 'tables path is lost, please provide the correct file path like dev_tables.json/test_tables.json'
        assert os.path.exists(databases_path), 'Database path is lost, please provide the correct file path like data/dev_databases'
        knowledge = {}
        with open(data_path, 'r', encoding='utf8') as pre_file:
            pre_data = json.load(pre_file)
            for line in tqdm(pre_data, desc='Knowledge pre-production'):
                db_name = line['db_id']
                if db_name in knowledge.keys():
                    continue
                tables = self.select_tables_names(databases_path, db_name)
                tables_columns_info = {}
                for table in tables:
                    columns = self.select_columns(databases_path, db_name, table)

                    tables_columns_info[table] = columns
                knowledge[db_name] = {'tables':tables_columns_info}
                knowledge[db_name]['foreign_keys'] = []
                try:
                    knowledge[db_name]['foreign_keys'] = self.knowledge_json[db_name]['foreign_keys']
                except:
                    print("Failed to load foreign_keys.")
        self.save_knowledge(save_path, knowledge)
        return knowledge

    def load_knowledge(self, save_path):
        with open(save_path, 'r', encoding='utf8') as kfile:
            self.knowledge = json.load(kfile)
            # print("load saved knowledge sucess")

    def select_tables_names(self, databases_path, db_name):
        db_path = databases_path  + '/' + db_name + '/' + db_name + '.sqlite'
        assert os.path.exists(db_path), 'db_path is lost: '+db_path+', please provide the correct file path xx/xyx.sqlite' 
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        tables = [table[0] for table in tables if table[0] != 'sqlite_sequence'] 
        

        cursor.close()
        conn.close()
        return tables
    
    def select_columns(self, databases_path, db_name, table):
        db_path = databases_path  + '/' + db_name + '/' + db_name + '.sqlite'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info('{}');".format(table))
        columns = cursor.fetchall()
        des_knowledge = self.select_columns_knowledge(databases_path, db_name, table)
        save_col = {}
        for column in columns:
            cid = column[0]
            cname = column[1]
            ctype = column[2]
            notnull = column[3]
            dflt_value = column[4]
            primary_key = column[5]
            column_value = self.select_column_value(cursor, table, cname, ctype)
            full_column_name = ''
            column_desc = ''
            value_desc = ''
            if des_knowledge:
                try:
                    column_desc = des_knowledge[cname.lower()]["column_description"]
                    value_desc = des_knowledge[cname.lower()]["value_description"]
                except:
                    print("Failed to load description: "+ db_name+"/" + table +"/"+ cname)
            try:
                full_column_name = self.knowledge_json[db_name]['tables'][table.lower()][cname.lower()]['full_column_name']
            except:
                print("Failed to load full_column_name: "+ db_name+"/" + table +"/"+ cname)

            save_col[cname] = {
                "full_column_name":full_column_name,
                "column_desc":column_desc,
                "ctype":ctype,
                "notnull":notnull,
                "dflt_value":dflt_value,
                "primary_key":primary_key,
                "examples":column_value,
                "value_desc":value_desc
            }
        return save_col
    
    # TODO
    def select_column_value(self, cursor, table, column_name, column_type):

        sql = f"SELECT `{column_name}` FROM `{table}` GROUP BY `{column_name}` ORDER BY COUNT(*) DESC"
        cursor.execute(sql)
        values = cursor.fetchall()
        values = [value[0] for value in values]

        values_str = ''
        # try to get value examples str, if exception, just use empty str
        try:
            values_str = self.get_value_examples_str(values, column_type)
        except Exception as e:
            print(f"\nerror: get_value_examples_str failed, Exception:\n{e}\n")
        return values_str

    def select_columns_knowledge(self, databases_path, db_name, table):
        db_path = databases_path + '/' +  db_name + '/' + 'database_description' + '/' + table + '.csv'
        try:
            with open(db_path, newline='', encoding='utf-8-sig', errors='ignore') as csvfile:
                reader = csv.DictReader(csvfile)

                headers_f = reader.fieldnames
                headers_r= ['original_column_name', 'column_name', 'column_description', 'data_format', 'value_description']

                columns = {}
                for row in reader:
                    for i in range(len(headers_r)):
                        original_column_name = str(row['original_column_name']).replace('\u2022', '')
                        column_description = str(row['column_description']).replace('\u2022', '')
                        value_description = str(row['value_description']).replace('\u2022', '')
                        columns[original_column_name.lower().strip()] = {
                            "column_description":column_description.strip(),
                            "value_description":value_description.strip()
                        }
                return columns
        except FileNotFoundError:
            print(db_path + ' not find')

        except Exception as e:
            return {}


    def select_column_full_names_and_fk(self, tables_json_path):
        assert os.path.exists(tables_json_path), 'tables path is lost, please provide the correct file path like dev_tables.json/test_tables.json'
        with open(tables_json_path, 'r', encoding='utf8') as file:
            extra_info = json.load(file)
            result = {}
            for item in extra_info:
                db_id = item['db_id']
                table_names = item['table_names']
                column_names_original = item['column_names_original']
                full_column_names = item['column_names']
                foreign_keys = item['foreign_keys']
                tables_info = {}
                keys_info = []
                for tidx in range(len(table_names)):
                    cols_info = {}
                    for cidx in range(len(column_names_original)):
                        idx, column_names = column_names_original[cidx]
                        if idx == tidx:
                            cols_info[column_names.lower()] = {
                                "full_column_name":full_column_names[cidx][1].replace("_", " ")
                            }
                    tables_info[table_names[tidx].lower()] = cols_info
                for f_key in foreign_keys:
                    first_key = f_key[0]
                    second_key = f_key[1]
                    first_table_id,  first_coloum = column_names_original[first_key]
                    second_table_id,  second_coloum = column_names_original[second_key]
                    first_table, second_table =  table_names[first_table_id], table_names[second_table_id]
                    foreign_key_des = self.str_standardization(first_table) + '.' + self.str_standardization(first_coloum) + \
                                        '=' + self.str_standardization(second_table) + '.' + self.str_standardization(second_coloum)
                    keys_info.append(foreign_key_des)

                result[db_id] = {"tables":tables_info}
                # result[db_id] = {"primary_keys":tables_info}
                result[db_id]['foreign_keys'] = keys_info
                # print(keys_info)
            return result

    def str_standardization(self, input):
        data = input.split(' ')
        if len(data) > 1:
            return '`' +  input + '`'
        else:
            return input               

    # TODO
    def get_value_examples_str(self, values, col_type):
        if not values:
            return ''
        # if len(values) > 10 and col_type in ['INTEGER', 'REAL', 'NUMERIC', 'FLOAT', 'INT']:
        #     return ''
        
        vals = []
        has_null = False
        for v in values:
            if v is None:
                has_null = True
            else:
                tmp_v = str(v).strip()
                if tmp_v == '':
                    continue
                else:
                    vals.append(v)
        if not vals:
            return ''
        
        # drop meaningless values
        if col_type in ['TEXT', 'VARCHAR']:
            new_values = []
            
            for v in vals:
                if not isinstance(v, str):
                    
                    new_values.append(v)
                else:
                    if v == '': # exclude empty string
                        continue
                    elif ('https://' in v) or ('http://' in v): # exclude url
                        return ''
                    elif is_email(v): # exclude email
                        return ''
                    else:
                        new_values.append(v)
            vals = new_values
            tmp_vals = [len(str(a)) for a in vals]
            if not tmp_vals:
                return ''
            max_len = max(tmp_vals)
            if max_len > 50:
                return ''
        
        if not vals:
            return ''
        
        vals = vals[:5]

        is_date_column = is_valid_date_column(vals)
        if is_date_column:
            vals = vals[:1]

        if has_null:
            vals.insert(0, None)
        
        val_str = str(vals)
        return val_str
    
    def save_knowledge(self, path, knowledge):

        dir_name, file_name = os.path.split(path)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(path,'w',encoding='utf8') as fwirte:
            json.dump(knowledge, fwirte, indent=2, ensure_ascii=False)

    
    
if __name__ == '__main__':
    knowledge = Knowledge(
        './data/bird/dev_process.json', 
        './data/dev/dev_tables.json',
        './data/dev/dev_databases',
        './data/pre_knowledge/knowledge.json')
    
