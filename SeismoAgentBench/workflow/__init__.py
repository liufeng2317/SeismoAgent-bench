"""End-to-end orchestration for task execution and output scoring."""

from .pipeline import evaluate_run, run_task

__all__ = ["evaluate_run", "run_task"]
