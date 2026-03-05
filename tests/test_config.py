"""
Tests for config.py — verifies all paths and settings load correctly.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config


def test_paths_exist():
    assert os.path.isdir(config.BASE_DIR), "BASE_DIR does not exist"
    assert os.path.isdir(config.MODELS_DIR), "models/ directory missing"
    assert os.path.isdir(config.DATA_DIR), "data/ directory missing"


def test_settings_are_valid():
    assert config.N_CTX > 0, "N_CTX must be positive"
    assert config.N_THREADS > 0, "N_THREADS must be positive"
    assert config.MAX_ITERATIONS > 0, "MAX_ITERATIONS must be positive"
    assert config.EXECUTION_TIMEOUT > 0, "EXECUTION_TIMEOUT must be positive"


def test_supported_extensions_not_empty():
    assert len(config.SUPPORTED_EXTENSIONS) > 0


def test_ignored_dirs_not_empty():
    assert len(config.IGNORED_DIRS) > 0


if __name__ == "__main__":
    test_paths_exist()
    test_settings_are_valid()
    test_supported_extensions_not_empty()
    test_ignored_dirs_not_empty()
    print("✅ All config tests passed.")
