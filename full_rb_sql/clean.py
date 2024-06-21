from utils import *
import json
import codecs
import re

def double_check(sql):
    if sql.startswith("SELECT") or sql.startswith("WITH"):
        return sql
    select_list = sql.split("SELECT")
    pos = 0
    for i  in range(len(select_list)):
        if i >=1:
            if not select_list[i-1].strip().endswith("("):
                pos = i
    sql = select_list[pos:]
    sql = "SELECT " + "SELECT".join(sql).strip()
    return sql

def select_final(sql,substring):
    pos = find_last_two_occurrences(sql, substring)
    if len(pos)==2:
        start, end = pos
        return  sql[start:end]
    else:
       return ""

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

def parse_sql_from_string(text):
    pattern = r'```sql\((.*?)```'
    matches = re.findall(pattern, text)

    if matches:
        last_match = matches[-1]
        return last_match
    else:
        return "No SQL found in the input string"


def parse_single_sql(res: str) -> str: 
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


