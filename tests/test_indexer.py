import unittest
import os
import tempfile
import hey_dongle.indexer as indexer
import config

class TestIndexer(unittest.TestCase):
    def test_1_build_index_finds_supported_files(self):
        """build_index finds supported files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files
            with open(os.path.join(temp_dir, "main.py"), "w", encoding="utf-8") as f:
                f.write("print('hello')\n")
            with open(os.path.join(temp_dir, "index.js"), "w", encoding="utf-8") as f:
                f.write("console.log('hello');\n")
            with open(os.path.join(temp_dir, "styles.css"), "w", encoding="utf-8") as f:
                f.write("body { color: red; }\n")
                
            index = indexer.build_index(temp_dir)
            
            self.assertEqual(index["total_files"], 3)
            paths = [f["path"] for f in index["files"]]
            self.assertIn("main.py", paths)
            self.assertIn("index.js", paths)
            self.assertIn("styles.css", paths)

    def test_2_build_index_skips_excluded_directories(self):
        """build_index skips excluded directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "app.py"), "w", encoding="utf-8") as f:
                f.write("print('app')\n")
            
            node_modules = os.path.join(temp_dir, "node_modules")
            os.makedirs(node_modules, exist_ok=True)
            with open(os.path.join(node_modules, "package.js"), "w", encoding="utf-8") as f:
                f.write("console.log('package');\n")
                
            index = indexer.build_index(temp_dir)
            
            self.assertEqual(index["total_files"], 1)
            self.assertEqual(index["files"][0]["path"], "app.py")

    def test_3_build_index_skips_unsupported_extensions(self):
        """build_index skips unsupported extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "main.py"), "w", encoding="utf-8") as f:
                f.write("print('hello')\n")
            with open(os.path.join(temp_dir, "image.png"), "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n")
            with open(os.path.join(temp_dir, "video.mp4"), "wb") as f:
                f.write(b"video data")
                
            index = indexer.build_index(temp_dir)
            
            self.assertEqual(index["total_files"], 1)
            self.assertEqual(index["files"][0]["path"], "main.py")

    def test_4_get_context_summary_fits_within_budget(self):
        """get_context_summary fits within budget."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a ton of fake files to bloat the context summary
            for i in range(50):
                with open(os.path.join(temp_dir, f"file_{i}.py"), "w", encoding="utf-8") as f:
                    f.write("# " * 200 + "\n") # long line to bloat size slightly

            index = indexer.build_index(temp_dir)
            
            # temporarily artificially shrink the config budget so we hit truncation fast
            old_budget = config.CONTEXT_BUDGET_CHARS
            config.CONTEXT_BUDGET_CHARS = 1000
            
            summary = indexer.get_context_summary(index)
            
            config.CONTEXT_BUDGET_CHARS = old_budget
            
            self.assertLessEqual(len(summary), 1000 + 100) # + margin for the truncation label appending
            self.assertIn("... and", summary)

    def test_5_get_file_content_returns_correct_content(self):
        """get_file_content returns correct content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_content = "def test():\n    pass\n"
            with open(os.path.join(temp_dir, "main.py"), "w", encoding="utf-8") as f:
                f.write(test_content)
                
            index = indexer.build_index(temp_dir)
            
            content = indexer.get_file_content(index, "main.py")
            
            self.assertEqual(content, test_content)
