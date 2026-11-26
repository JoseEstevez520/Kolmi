"""The compiler is a bench measurement and does not gate the pass."""
import json
from types import SimpleNamespace

from evals.run_piece_evals import compile_piece


def test_bench_reports_compiler_errors(monkeypatch):
    def run(args, **kwargs):
        assert args[0] == "node"
        assert kwargs["input"] == "a piece"
        assert kwargs["timeout"] == 20
        return SimpleNamespace(returncode=0, stdout=json.dumps({"problems": ["Invalid expression"]}))
    monkeypatch.setattr("evals.run_piece_evals.subprocess.run", run)
    assert compile_piece("a piece") == ["Invalid expression"]
