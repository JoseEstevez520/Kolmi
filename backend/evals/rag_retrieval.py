"""How well does the search by meaning find the page that holds the answer?

Each question in rag_questions.json names the page (node_id) that answers it. The app's own
search (app.rag.search) returns chunks; they are collapsed to pages in rank order, and we report
recall@k at page level (is the right page among the first k distinct pages) and MRR, overall and
per kind (exact, paraphrase, concept), then the questions that missed.

Run from backend/ with the app's environment (SUPABASE_URL, SUPABASE_SERVICE_KEY, CLASS_CODE,
EMBEDDING_API_KEY...), the same as the server. It only reads the database.

    .venv/bin/python -m evals.rag_retrieval
    .venv/bin/python -m evals.rag_retrieval --only concept --verbose --json out.json

Questions are made with `python -m evals.make_rag_questions`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app.rag import search
from app.supabase_client import get_client

QUESTIONS = Path(__file__).with_name("rag_questions.json")
KS = (1, 3, 8)
KINDS = ("exact", "paraphrase", "concept")


def collapse(chunks: list[dict[str, Any]]) -> list[int]:
    """Page ids in rank order, each once."""
    pages: list[int] = []
    for chunk in chunks:
        if chunk["node_id"] not in pages:
            pages.append(chunk["node_id"])
    return pages


def recall_at(pages: list[int], expected: int, k: int) -> bool:
    return expected in pages[:k]


def reciprocal_rank(pages: list[int], expected: int) -> float:
    return 1 / (pages.index(expected) + 1) if expected in pages else 0.0


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(results)
    if not n:
        return {"n": 0, **{f"recall@{k}": 0.0 for k in KS}, "mrr": 0.0}
    return {
        "n": n,
        **{f"recall@{k}": sum(recall_at(r["pages"], r["node_id"], k) for r in results) / n for k in KS},
        "mrr": sum(reciprocal_rank(r["pages"], r["node_id"]) for r in results) / n,
    }


def line(label: str, s: dict[str, Any]) -> str:
    cells = "  ".join(f"{s[f'recall@{k}']:.2f}" for k in KS)
    return f"{label:11} n={s['n']:<3}  {cells}  mrr={s['mrr']:.3f}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--k", type=int, default=max(KS), help="chunks to ask the search for")
    parser.add_argument("--only", choices=KINDS, help="only this kind")
    parser.add_argument("--verbose", action="store_true", help="print every question's rank")
    parser.add_argument("--json", metavar="FILE", help="write the numbers and the misses here")
    options = parser.parse_args()

    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    questions = [q for q in questions if not options.only or q["kind"] == options.only]
    client = get_client()
    titles = {r["id"]: r["title"] for r in client.table("nodes").select("id, title").execute().data}

    results = [{**q, "pages": collapse(search(client, q["question"], options.k))} for q in questions]
    if results and not any(r["pages"] for r in results):
        print("The search returned nothing: is EMBEDDING_API_KEY set?", file=sys.stderr)
        return 2

    def name(node_id: int) -> str:
        return f"{titles.get(node_id, '?')} ({node_id})"

    report: dict[str, Any] = {"k": options.k, "overall": summarize(results)}
    report["by_kind"] = {
        kind: summarize([r for r in results if r["kind"] == kind]) for kind in KINDS if not options.only or kind == options.only
    }
    misses = [r for r in results if not recall_at(r["pages"], r["node_id"], options.k)]
    report["misses"] = [
        {
            "id": r["id"], "question": r["question"], "kind": r["kind"], "expected": name(r["node_id"]),
            "retrieved": [name(p) for p in r["pages"][:3]],
        }
        for r in misses
    ]

    if options.verbose:
        for r in results:
            rank = r["pages"].index(r["node_id"]) + 1 if r["node_id"] in r["pages"] else "-"
            print(f"{r['id']}  {r['kind']:10}  rank={rank}  {r['question']}")
        print()
    print(f"{'':11} {'':6}  " + "  ".join(f"@{k:<3}" for k in KS))
    print(line("overall", report["overall"]))
    for kind, s in report["by_kind"].items():
        print(line(kind, s))
    if misses:
        print(f"\nNot in the first {options.k} pages ({len(misses)}):")
        for m in report["misses"]:
            got = "; ".join(m["retrieved"]) or "nothing"
            print(f"  {m['id']}  [{m['kind']}] {m['question']}\n      wanted {m['expected']}\n      got    {got}")
    if options.json:
        Path(options.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
