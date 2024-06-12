import os
import random

from colbert.utils.parser import Arguments
from colbert.utils.runs import Run

from colbert.evaluation.loaders import load_colbert, load_topK, load_qrels
from colbert.evaluation.loaders import load_queries, load_topK_pids, load_collection
from colbert.evaluation.ranking import evaluate
from colbert.evaluation.metrics import evaluate_recall
from colbert.modeling.inference import ModelInference


def main():
    random.seed(12345)

    parser = Arguments(description='inference')

    parser.add_model_parameters()
    parser.add_model_inference_parameters()

    parser.add_argument('--depth', dest='depth', required=False, default=None, type=int)

    args = parser.parse()

    args.colbert, args.checkpoint = load_colbert(args)

    inference = ModelInference(args.colbert, amp=args.amp)
    query = ["Name movie titles released in year 1945. Sort the listing by the descending order of movie popularity."]
    document = ["name:lists||content:\"user_id:integer\"|\"list_id:integer\"|\"list_title:text\"|\"list_movie_number:integer\"|\"list_update_timestamp_utc:text\"|\"list_creation_timestamp_utc:text\"|\"list_followers:integer\"|\"list_url:text\"|\"list_comments:integer\"|\"list_description:text\"|\"list_cover_image_url:text\"|\"list_first_image_url:text\"|\"list_second_image_url:text\"|\"list_third_image_url:text\"|"]

    Q = inference.queryFromText(query)
    D = inference.docFromText(document)
    print(Q.size())
    print(D.size())
    score = (-1.0 * ((Q.unsqueeze(2) - D.unsqueeze(1))**2).sum(-1)).max(-1).values.sum(-1)
    #score = (Q @ D.permute(0, 2, 1)).max(2).values.sum(1)
    print(score)


    #evaluate(args)


if __name__ == "__main__":
    main()
