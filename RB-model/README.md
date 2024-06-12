The RB-models are designed base on [ColBERT](https://github.com/stanford-futuredata/ColBERT/tree/colbertv1). The environment and data formats are the same as ColBERT.

User should construct datasets from the original BIRD and Spider.

Here, we provide some processed datasets and examples about how to train and use RB-models as follows:
## Set PYTHONPATH
```
export PYTHONPATH=$PYTHONPATH:/.../RB-model
```

# Table-Retriever

## Training

```
python ./colbert/train.py --amp --doc_maxlen 180 --mask-punctuation --bsize 32 --accum 1 \
--triples ./bird_table_train/triples.train.tsv \
--collection ./bird_table_train/collection.train.tsv \
--queries ./bird_table_train/queries.train.tsv \
--root ./experiments/ --experiment bird --similarity cosine --run bird.cosine
```
The trained model is reserved as ```./experiments/bird/train.py/bird.cosine/checkpoints/xxx.dnn```

## Reference

```
python ./colbert/calculate_sim_colbert.py --amp --doc_maxlen 180 --mask-punctuation \
--checkpoint ./experiments/bird/train.py/bird.cosine/checkpoints/xxx.dnn \
--root ./experiments/ --experiment bird
```
User can edit the the last line of```calculate_sim_colbert.py``` to modify the result file address.

# Column-Retriever

## Training

```
python ./colbert/train.py --amp --doc_maxlen 180 --mask-punctuation --bsize 32 --accum 1 \
--triples ./bird_columnName_train/triples.train.tsv \
--collection ./bird_columnName_train/columns.train.tsv \
--queries ./bird_columnName_train/queries.train.tsv \
--root ./experiments/ --experiment bird_columns --similarity cosine --run bird_columns.cosine
```
The trained model is reserved as ```./experiments/bird_columns/train.py/bird_columns.cosine/checkpoints/xxx.dnn```

## Reference

```
python ./colbert/calculate_sim_colbert_column.py --amp --doc_maxlen 180 --mask-punctuation \
--checkpoint ./experiments/bird_columns/train.py/bird_columns.cosine/checkpoints/xxx.dnn \
--root ./experiments/ --experiment bird
```
User can edit the the last line of```calculate_sim_colbert_column.py``` to modify the result file address.

# SQL-Skeleton-Retriever

## Training

```
python ./colbert/train.py --amp --doc_maxlen 180 --mask-punctuation --bsize 32 --accum 1 \
--triples ./bird_sql_skeleton_train/triples_sqls.train.tsv \
--collection ./bird_sql_skeleton_train/sqls_skeleton.train.tsv \
--queries ./bird_sql_skeleton_train/queries.train.tsv \
--root ./experiments/ --experiment bird_sql_skeleton --similarity cosine --run bird_sql_skeleton.cosine
```
The trained model is reserved as ```./experiments/bird_sql_skeleton/train.py/bird_sql_skeleton.cosine/checkpoints/xxx.dnn```

## Reference

```
python ./colbert/calculate_sim_colbert_sql.py --amp --doc_maxlen 180 --mask-punctuation \
--checkpoint ./experiments/bird_sql_skeleton/train.py/bird_sql_skeleton.cosine/checkpoints/xxx.dnn \
--root ./experiments/ --experiment bird
```
User can edit the the last line of```calculate_sim_colbert_sql.py``` to modify the result file address.

