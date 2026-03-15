import unittest
import os
import tempfile
import hey_dongle.tools as tools

class TestTools(unittest.TestCase):
    def test_1_read_file_returns_correct_content(self):
        """read_file returns correct content including metadata header."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            test_content = "line 1\nline 2\nline 3"
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(test_content)
                
            result = tools.read_file(file_path)
            
            self.assertIn("test.txt", result)
            self.assertIn("3 lines", result)
            self.assertIn(test_content, result)

    def test_2_read_file_returns_error_for_missing_file(self):
        """read_file returns error for missing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "definitely_does_not_exist.py")
            result = tools.read_file(file_path)
            
            self.assertTrue(result.startswith("Error:"))

    def test_3_write_file_creates_new_file(self):
        """write_file creates a new file upon approval."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "new_file.txt")
            content = "hello world"
            
            result = tools.write_file(file_path, content, prompt_fn=lambda a, d: True)
            
            self.assertTrue(result.startswith("Success"))
            self.assertTrue(os.path.exists(file_path))
            
            with open(file_path, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), content)

    def test_4_write_file_respects_denial(self):
        """write_file stops execution if prompt denies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "blocked_file.txt")
            
            result = tools.write_file(file_path, "data", prompt_fn=lambda a, d: False)
            
            self.assertIn("denied", result.lower())
            self.assertFalse(os.path.exists(file_path))

    def test_5_apply_patch_modifies_correct_text(self):
        """apply_patch alters text selectively based on patch markers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "script.py")
            original = "def foo():\n    return False\n"
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(original)
                
            patch = "<<<FIND>>>\n    return False\n<<<REPLACE>>>\n    return True\n<<<END>>>"
            
            result = tools.apply_patch(file_path, patch, prompt_fn=lambda a, d: True)
            
            self.assertTrue(result.startswith("Success"))
            with open(file_path, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), "def foo():\n    return True\n")

    def test_6_search_codebase_finds_matches(self):
        """search_codebase correctly filters contents to locate substrings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "match.py"), "w", encoding="utf-8") as f:
                f.write("def my_secret_function():\n    pass\n")
            with open(os.path.join(temp_dir, "no_match.py"), "w", encoding="utf-8") as f:
                f.write("def other_function():\n    pass\n")
                
            result = tools.search_codebase("secret_function", project_dir=temp_dir)
            
            self.assertIn("match.py", result)
            self.assertNotIn("no_match.py", result)
            self.assertIn("my_secret_function", result)
