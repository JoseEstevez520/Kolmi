from __future__ import annotations

import argparse
import sys

from ..supabase_client import get_client
from .embeddings import get_embedder
from .index import reindex_all


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.rag", description="Kolmi's search index.")
    commands = parser.add_subparsers(dest="command", required=True)
    reindex = commands.add_parser("reindex", help="Index every page whose Markdown changed.")
    reindex.add_argument(
        "--force",
        action="store_true",
        help="Embed every page again, changed or not (after switching models).",
    )
    args = parser.parse_args()

    if get_embedder() is None:
        sys.exit("EMBEDDING_API_KEY is not set: search by meaning is off.")
    indexed = reindex_all(get_client(), force=args.force)
    print(f"Indexed {indexed} page{'' if indexed == 1 else 's'}.")


if __name__ == "__main__":
    main()
