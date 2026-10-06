"""Write evals/rag_questions.json: questions per page, made by the instance's model.

Reads the pages from Supabase (read only) and asks the model for two questions per page, from
the page text alone. Run from backend/ with the environment set (see rag_retrieval.py):

    .venv/bin/python -m evals.make_rag_questions --pages 28
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from app.agents import get_llm
from app.supabase_client import get_client

OUT = Path(__file__).with_name("rag_questions.json")
SYSTEM = (
    "You write search questions for testing a retrieval system over class notes. Given one page, "
    "write 2 questions in Spanish that a student would type to find it, each answered by the page. "
    'Return JSON: {"questions": [{"question": str, "kind": "exact"|"paraphrase"|"concept"}]}. '
    "exact: uses a specific term that appears in the page. paraphrase: the same idea in different "
    "words than the page. concept: a conceptual question the page answers, without its title words. "
    "Use two different kinds. Never include the page title."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pages", type=int, default=28)
    parser.add_argument("--seed", type=int, default=7)
    options = parser.parse_args()

    rows = get_client().table("nodes").select("id, title, content_md").eq("kind", "page").execute().data
    rows = [r for r in rows if len((r.get("content_md") or "").strip()) > 400]
    random.Random(options.seed).shuffle(rows)
    llm, out = get_llm(), []
    for row in rows[: options.pages]:
        try:
            data = llm.complete_json(SYSTEM, f"# {row['title']}\n\n{row['content_md'][:4000]}")
        except Exception as exc:
            print(f"skip {row['id']}: {exc}", file=sys.stderr)
            continue
        for q in data.get("questions", [])[:2]:
            text, kind = (q.get("question") or "").strip(), q.get("kind")
            if text and kind in ("exact", "paraphrase", "concept") and row["title"].lower() not in text.lower():
                out.append({"id": f"q{len(out) + 1:02}", "question": text, "node_id": row["id"], "kind": kind})
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(out)} questions over {len({q['node_id'] for q in out})} pages -> {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
