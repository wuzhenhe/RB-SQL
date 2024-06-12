import json
content = 0
with open("../spider/test.processed_20240306_6.json",'r', encoding="utf-8") as f:
    content = json.load(f)

correct = 0
all = 0
for i in range(len(content)):
    table_names = content[i]["table_names"]
    retrieval_tables = content[i]["retrieval_tables"]
    all = all + 1
    correct = correct + 1
    for j in range(len(table_names)):
        if table_names[j] not in retrieval_tables:
            correct = correct - 1
            break
print(float(correct)/float(all))

'''correct = 0
all = 0
for i in range(len(content)):
    table_names = content[i]["table_names"]
    retrieval_tables = content[i]["retrieval_tables"]
    all = all + len(table_names)
    correct = correct + len(table_names)
    for j in range(len(table_names)):
        if table_names[j] not in retrieval_tables:
            correct = correct - 1


print(float(correct)/float(all))



correct = 0
all = 0
for i in range(len(content)):
    if content[i]["difficulty"]=="simple":
        table_names = content[i]["table_names"]
        retrieval_tables = content[i]["retrieval_tables"]
        all = all + 1
        correct = correct + 1
        for j in range(len(table_names)):
            if table_names[j] not in retrieval_tables:
                correct = correct - 1
                break
print("simple:",float(correct)/float(all))

correct = 0
all = 0
for i in range(len(content)):
    if content[i]["difficulty"]=="simple":
        table_names = content[i]["table_names"]
        retrieval_tables = content[i]["retrieval_tables"]
        all = all + len(table_names)
        correct = correct + len(table_names)
        for j in range(len(table_names)):
            if table_names[j] not in retrieval_tables:
                correct = correct - 1

print("simple:",float(correct)/float(all))

correct = 0
all = 0
for i in range(len(content)):
    if content[i]["difficulty"]=="moderate":
        table_names = content[i]["table_names"]
        retrieval_tables = content[i]["retrieval_tables"]
        all = all + 1
        correct = correct + 1
        for j in range(len(table_names)):
            if table_names[j] not in retrieval_tables:
                correct = correct - 1
                break
print("moderate",float(correct)/float(all))

correct = 0
all = 0
for i in range(len(content)):
    if content[i]["difficulty"]=="moderate":
        table_names = content[i]["table_names"]
        retrieval_tables = content[i]["retrieval_tables"]
        all = all + len(table_names)
        correct = correct + len(table_names)
        for j in range(len(table_names)):
            if table_names[j] not in retrieval_tables:
                correct = correct - 1

print("moderate:",float(correct)/float(all))

correct = 0
all = 0
for i in range(len(content)):
    if content[i]["difficulty"]=="challenging":
        table_names = content[i]["table_names"]
        retrieval_tables = content[i]["retrieval_tables"]
        all = all + 1
        correct = correct + 1
        for j in range(len(table_names)):
            if table_names[j] not in retrieval_tables:
                correct = correct - 1
                break
print("challenging:",float(correct)/float(all))

correct = 0
all = 0
for i in range(len(content)):
    if content[i]["difficulty"]=="challenging":
        table_names = content[i]["table_names"]
        retrieval_tables = content[i]["retrieval_tables"]
        all = all + len(table_names)
        correct = correct + len(table_names)
        for j in range(len(table_names)):
            if table_names[j] not in retrieval_tables:
                correct = correct - 1

print("challenging:",float(correct)/float(all))'''

