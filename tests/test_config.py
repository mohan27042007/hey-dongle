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
    assert config.EXECUTION_TIMEOUT_SECONDS > 0, "EXECUTION_TIMEOUT_SECONDS must be positive"


def test_supported_extensions_not_empty():
    assert len(config.SUPPORTED_EXTENSIONS) > 0


def test_ignored_dirs_not_empty():
    assert len(config.SKIP_DIRS) > 0


def test_model_path_constructed_correctly():
    assert config.MODEL_PATH == os.path.join(config.MODELS_DIR, config.MODEL_FILENAME)


def test_model_filename_ends_with_gguf():
    assert config.MODEL_FILENAME.endswith('.gguf')


def test_validate_model_raises_file_not_found():
    import hey_dongle.infer as infer
    original = config.MODEL_PATH
    config.MODEL_PATH = "/nonexistent/fake_model.gguf"
    try:
        try:
            infer.validate_model()
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass
    finally:
        config.MODEL_PATH = original


def test_validate_model_raises_value_error():
    import tempfile
    import hey_dongle.infer as infer
    original = config.MODEL_PATH
    # Create a temp file with non-.gguf extension
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(b"x" * 200)  # > 100 MB check won't fire since it's tiny
        tmp_path = f.name
    try:
        config.MODEL_PATH = tmp_path
        try:
            infer.validate_model()
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
    finally:
        config.MODEL_PATH = original
        import os
        os.unlink(tmp_path)


if __name__ == "__main__":
    test_paths_exist()
    test_settings_are_valid()
    test_supported_extensions_not_empty()
    test_ignored_dirs_not_empty()
    test_model_path_constructed_correctly()
    test_model_filename_ends_with_gguf()
    test_validate_model_raises_file_not_found()
    test_validate_model_raises_value_error()
    print("All config tests passed.")
