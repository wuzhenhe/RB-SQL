import os
import re
# from const import *
import json

import asyncio
import sqlite3
import threading
from typing import Tuple, Any, List, Set
from itertools import product
from collections import defaultdict
import tqdm
import random
from parse import get_all_preds_for_execution, remove_distinct
import time
import pickle as pkl
import subprocess
from itertools import chain
def check_path(file_path):
    assert os.path.exists(file_path), 'the path is not found:' + file_path

def clean_result(result):
    # TODO 清洗方法待细化
    if "```sql" in result:
        result = result.split("```sql")[1].split("```")[0]
    else:
        result = result
    result = result.replace("-- SQL Type: SQLite","").replace("-- Corrected SQL","").replace("\n"," ").replace("\r"," ").strip().rstrip(';')
    result = re.sub(r'\s+', ' ', result)
    # result = result.replace("-- SQL Type: SQLite","").replace("-- Corrected SQL","").strip().rstrip(';')
    return result

   
def parse_qa_pairs_mac(res: str, end_pos=2333) -> list:
    lines = res.split('\n')
    qa_pairs = []
    # end_pos = -1
    # for idx, line in enumerate(lines):
    #     if 'final SQL' in line or 'final sql' in line:
    #         end_pos = idx
    # if end_pos == -1: return []
    end_pos = len(lines) if (end_pos == 2333) else end_pos
    for idx in range(0, end_pos):
        if re.findall(subq_pattern, lines[idx], re.IGNORECASE) != []:
            query = lines[idx]
            start_idx = -1
            for idx2 in range(idx + 1, end_pos):
                if '```' in lines[idx2]:
                    start_idx = idx2
                    break
            if start_idx == -1: return []
            for idx3 in range(start_idx + 1, end_pos):
                if '```' in lines[idx3]:
                    end_idx = idx3
                    break
            if end_idx == -1: return []
            answer = " ".join(lines[start_idx + 1: end_idx])
            qa_pairs.append((str(query), str(answer)))
            idx = end_idx
    return qa_pairs 

def parse_qa_pairs_mac_skeleton(res: str, end_pos=2333) -> list:
    lines = res.split('\n')
    qa_pairs = []
    # end_pos = -1
    # for idx, line in enumerate(lines):
    #     if 'final SQL' in line or 'final sql' in line:
    #         end_pos = idx
    # if end_pos == -1: return []
    end_pos = len(lines) if (end_pos == 2333) else end_pos
    for idx in range(0, end_pos):
        if re.findall(subq_pattern, lines[idx], re.IGNORECASE) != []:
            query = lines[idx]
            start_idx = -1
            flag = 0
            for idx2 in range(idx + 1, end_pos):
                if '```' in lines[idx2]:
                    if 'skeleton' in lines[idx2]:
                        flag = 1
                    else:
                        if flag == 1:
                            flag = 0
                            continue
                        else:
                            start_idx = idx2
                            break
            if start_idx == -1: return []
            for idx3 in range(start_idx + 1, end_pos):
                if '```' in lines[idx3]:
                    end_idx = idx3
                    break
            if end_idx == -1: return []
            answer = " ".join(lines[start_idx + 1: end_idx])
            qa_pairs.append((str(query), str(answer)))
            idx = end_idx
    return qa_pairs 


def parse_single_sql_mac(res: str) -> str:  # if do not need decompose, just one code block is OK!
    """Return SQL in markdown block"""
    lines = res.split('\n')
    iter, start_idx, end_idx = -1, -1, -1
    for idx in range(iter + 1, len(lines)):
        if '```' in lines[idx]:
            start_idx = idx
            break
    if start_idx == -1: return ""
    for idx in range(start_idx + 1, len(lines)):
        if '```' in lines[idx]:
            end_idx = idx
            break
    if end_idx == -1: return ""

    return " ".join(lines[start_idx + 1: end_idx])


def select_final_sql(sql,substring):
    pos = find_last_two_occurrences(sql, substring)
    if len(pos)==2:
        start, end = pos
        return  sql[start:end]
    else:
        return "not find" 


def find_last_two_occurrences(text, substring):
    positions = []
    start = 0
    while True:
        position = text.find(substring, start)
        if position == -1:
            break
        positions.append(position)
        start = position + 1
    if len(positions) >= 2:
        return positions[-2:]
    else:
        return []

def add_prefix(sql):
    if not sql.startswith('SELECT') and not sql.startswith('select'):
        sql = 'SELECT' + sql
    return sql

def load_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        print(f"load json file from {path}")
        return json.load(f)

def is_email(string):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    match = re.match(pattern, string)
    if match:
        return True
    else:
        return False

def is_valid_date_column(col_value_lst):
    for col_value in col_value_lst:
        if not is_valid_date(col_value):
            return False
    return True

def is_valid_date(date_str):
    if (not isinstance(date_str, str)):
        return False
    date_str = date_str.split()[0]
    if len(date_str) != 10:
        return False
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if re.match(pattern, date_str):
        year, month, day = map(int, date_str.split('-'))
        if year < 1 or month < 1 or month > 12 or day < 1 or day > 31:
            return False
        else:
            return True
    else:
        return False


