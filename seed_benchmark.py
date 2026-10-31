#!/usr/bin/env python3
"""
seed_benchmark.py - Root runner for performance benchmarks.
"""
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.seed_benchmark import run_benchmark

if __name__ == "__main__":
    results = run_benchmark()
    sys.exit(0 if all(t < 2.0 for t in results.values()) else 1)
