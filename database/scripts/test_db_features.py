#!/usr/bin/env python3
"""
Convenience launcher pointing to the main test_sms.py runner.
"""
import runpy
import os

root_test = os.path.join(os.path.dirname(__file__), "..", "..", "test_sms.py")
runpy.run_path(root_test, run_name="__main__")
