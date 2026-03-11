import os
import unittest
import time
import config
from hey_dongle import infer

class TestInfer(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.model_exists = os.path.exists(config.MODEL_PATH)

    def setUp(self):
        if not self.model_exists:
            self.skipTest("Skipping - model not downloaded yet")

    def test_1_model_exists(self):
        # We check in setUp, but this test explicitly asserts it if it runs.
        self.assertTrue(os.path.exists(config.MODEL_PATH))

    def test_2_model_loads(self):
        start_time = time.time()
        model = infer.load_model()
        end_time = time.time()
        
        self.assertIsNotNone(model)
        self.assertIsNotNone(infer._model)
        print(f"\nModel load time: {end_time - start_time:.2f}s")
        
        # Test get_model_info works
        info = infer.get_model_info()
        self.assertTrue(info["loaded"])
        self.assertEqual(info["n_ctx"], config.N_CTX)
        self.assertEqual(info["n_threads"], config.N_THREADS)

    def test_3_basic_text_completion(self):
        messages = [
            {"role": "user", "content": "Write a Python function that returns the sum of two numbers. Output only code."}
        ]
        response = infer.chat(messages)
        
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        self.assertIn("def", response) # Should contain a python function

    def test_4_tool_call_parsing(self):
        messages = [
            {"role": "system", "content": "You are a helpful assistant with access to tools. When requested to use a tool, always format your response as a valid tool call."},
            {"role": "user", "content": "Read the contents of the file named 'main.py'."}
        ]
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Reads the contents of a given file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "The path to the file to read"}
                        },
                        "required": ["path"]
                    }
                }
            }
        ]
        
        # It's difficult to guarantee the model uses the tool 100% in a test 
        # without fine-tuning, but we can verify our wrapper handles the response without crashing
        response = infer.chat_with_tools(messages, tools)
        
        # Must be either a generic string or a parsed tool dict
        self.assertIsInstance(response, (str, dict))
        
        if isinstance(response, dict):
            self.assertIn("tool", response)
            self.assertIn("args", response)
            
if __name__ == "__main__":
    unittest.main()
