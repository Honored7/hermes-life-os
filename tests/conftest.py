"""Shared test configuration — adds demo/ to Python path."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "demo"))

