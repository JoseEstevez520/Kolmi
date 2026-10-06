"""The retrieval eval's metrics: page collapsing, recall@k and MRR."""

from evals.rag_retrieval import collapse, recall_at, reciprocal_rank, summarize


def chunks(*ids):
    return [{"node_id": i} for i in ids]


def test_collapse_keeps_first_rank_of_each_page():
    assert collapse(chunks(3, 3, 5, 3, 7, 5)) == [3, 5, 7]
    assert collapse([]) == []


def test_recall_at_looks_at_distinct_pages():
    pages = collapse(chunks(1, 1, 1, 2))
    assert not recall_at(pages, 2, 1)
    assert recall_at(pages, 2, 2)
    assert not recall_at(pages, 9, 8)


def test_reciprocal_rank():
    assert reciprocal_rank([4, 5, 6], 4) == 1
    assert reciprocal_rank([4, 5, 6], 6) == 1 / 3
    assert reciprocal_rank([4, 5], 9) == 0


def test_summarize():
    results = [{"node_id": 1, "pages": [1, 2]}, {"node_id": 2, "pages": [1, 2]}, {"node_id": 3, "pages": [1]}]
    s = summarize(results)
    assert s["n"] == 3
    assert s["recall@1"] == 1 / 3
    assert s["recall@3"] == 2 / 3
    assert s["mrr"] == (1 + 0.5 + 0) / 3
    assert summarize([])["n"] == 0
