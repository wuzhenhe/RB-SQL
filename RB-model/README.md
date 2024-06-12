The RB-models are designed base on ColBERT. The environment and data formats are the same as ColBERT.

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
We can edit the the last line of```calculate_sim_colbert.py``` to modify the result file address.


## Data

This repository works directly with a simple **tab-separated file** format to store queries, passages, and top-k ranked lists.


* Queries: each line is `qid \t query text`.
* Collection: each line is `pid \t passage text`. 
* Top-k Ranking: each line is `qid \t pid \t rank`.

This works directly with the data format of the [MS MARCO Passage Ranking](https://github.com/microsoft/MSMARCO-Passage-Ranking) dataset. You will need the training triples (`triples.train.small.tar.gz`), the official top-1000 ranked lists for the dev set queries (`top1000.dev`), and the dev set relevant passages (`qrels.dev.small.tsv`). For indexing the full collection, you will also need the list of passages (`collection.tar.gz`).



## Training

Training requires a list of _<query, positive passage, negative passage>_ tab-separated triples.

You can supply **full-text** triples, where each line is `query text \t positive passage text \t negative passage text`. Alternatively, you can supply the query and passage **IDs** as a JSONL file `[qid, pid+, pid-]` per line, in which case you should specify `--collection path/to/collection.tsv` and `--queries path/to/queries.train.tsv`.


```
CUDA_VISIBLE_DEVICES="0,1,2,3" \
python -m torch.distributed.launch --nproc_per_node=4 -m \
colbert.train --amp --doc_maxlen 180 --mask-punctuation --bsize 32 --accum 1 \
--triples /path/to/MSMARCO/triples.train.small.tsv \
--root /root/to/experiments/ --experiment MSMARCO-psg --similarity l2 --run msmarco.psg.l2
```

You can use one or more GPUs by modifying `CUDA_VISIBLE_DEVICES` and `--nproc_per_node`.


## Validation

Before indexing into ColBERT, you can compare a few checkpoints by re-ranking a top-k set of documents per query. This will use ColBERT _on-the-fly_: it will compute document representations _during_ query evaluation.

This script requires the top-k list per query, provided as a tab-separated file whose every line contains a tuple `queryID \t passageID \t rank`, where rank is {1, 2, 3, ...} for each query. The script also accepts the format of MS MARCO's `top1000.dev` and `top1000.eval` and you can optionally supply relevance judgements (qrels) for evaluation. This is a tab-separated file whose every line has a quadruple _<query ID, 0, passage ID, 1>_, like `qrels.dev.small.tsv`.

Example command:

```
python -m colbert.test --amp --doc_maxlen 180 --mask-punctuation \
--collection /path/to/MSMARCO/collection.tsv \
--queries /path/to/MSMARCO/queries.dev.small.tsv \
--topk /path/to/MSMARCO/top1000.dev  \
--checkpoint /root/to/experiments/MSMARCO-psg/train.py/msmarco.psg.l2/checkpoints/colbert-200000.dnn \
--root /root/to/experiments/ --experiment MSMARCO-psg  [--qrels path/to/qrels.dev.small.tsv]
```


## Indexing

For fast retrieval, indexing precomputes the ColBERT representations of passages.

Example command:

```
CUDA_VISIBLE_DEVICES="0,1,2,3" OMP_NUM_THREADS=6 \
python -m torch.distributed.launch --nproc_per_node=4 -m \
colbert.index --amp --doc_maxlen 180 --mask-punctuation --bsize 256 \
--checkpoint /root/to/experiments/MSMARCO-psg/train.py/msmarco.psg.l2/checkpoints/colbert-200000.dnn \
--collection /path/to/MSMARCO/collection.tsv \
--index_root /root/to/indexes/ --index_name MSMARCO.L2.32x200k \
--root /root/to/experiments/ --experiment MSMARCO-psg
```

The index created here allows you to re-rank the top-k passages retrieved by another method (e.g., BM25).

We typically recommend that you use ColBERT for **end-to-end** retrieval, where it directly finds its top-k passages from the full collection. For this, you need FAISS indexing.


#### FAISS Indexing for end-to-end retrieval

For end-to-end retrieval, you should index the document representations into [FAISS](https://github.com/facebookresearch/faiss).

```
python -m colbert.index_faiss \
--index_root /root/to/indexes/ --index_name MSMARCO.L2.32x200k \
--partitions 32768 --sample 0.3 \
--root /root/to/experiments/ --experiment MSMARCO-psg
```


## Retrieval

In the simplest case, you want to retrieve from the full collection:

```
python -m colbert.retrieve \
--amp --doc_maxlen 180 --mask-punctuation --bsize 256 \
--queries /path/to/MSMARCO/queries.dev.small.tsv \
--nprobe 32 --partitions 32768 --faiss_depth 1024 \
--index_root /root/to/indexes/ --index_name MSMARCO.L2.32x200k \
--checkpoint /root/to/experiments/MSMARCO-psg/train.py/msmarco.psg.l2/checkpoints/colbert-200000.dnn \
--root /root/to/experiments/ --experiment MSMARCO-psg
```

You may also want to re-rank a top-k set that you've retrieved before with ColBERT or with another model. For this, use `colbert.rerank` similarly and additionally pass `--topk`.

If you have a large set of queries (or want to reduce memory usage), use **batch-mode** retrieval and/or re-ranking. This can be done by passing `--batch --retrieve_only` to `colbert.retrieve` and passing `--batch --log-scores` to colbert.rerank alongside `--topk` with the `unordered.tsv` output of this retrieval run.

Some use cases (e.g., building a user-facing search engines) require more control over retrieval. For those, you typically don't want to use the command line for retrieval. Instead, you want to import our retrieval API from Python and directly work with that (e.g., to build a simple REST API). Instructions for this are coming soon, but you will just need to adapt/modify the retrieval loop in [`colbert/ranking/retrieval.py#L33`](colbert/ranking/retrieval.py#L33).


## Releases

* v0.2.0: Sep 2020
* v0.1.0: June 2020

