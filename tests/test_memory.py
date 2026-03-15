import unittest
import hey_dongle.memory as memory

class TestMemory(unittest.TestCase):
    def setUp(self):
        """Reset the database connection singleton between tests."""
        memory._conn = None

    def test_1_init_db_creates_table(self):
        """init_db creates the table."""
        memory.init_db(":memory:")
        conn = memory._get_conn(":memory:")
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "messages")

    def test_2_save_and_load_round_trip(self):
        """save and load round trip."""
        memory.init_db(":memory:")
        session_id = "session_20260315_120000"
        
        memory.save_message(":memory:", session_id, "user", "Hello")
        memory.save_message(":memory:", session_id, "assistant", "Hi there")
        memory.save_message(":memory:", session_id, "user", "How are you?")
        
        messages = memory.load_session(":memory:", session_id)
        
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hello")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["content"], "Hi there")
        self.assertEqual(messages[2]["role"], "user")
        self.assertEqual(messages[2]["content"], "How are you?")

    def test_3_get_last_session(self):
        """get_last_session returns correct session."""
        memory.init_db(":memory:")
        
        # Test empty DB
        self.assertIsNone(memory.get_last_session(":memory:"))
        
        # Add messages to session A
        memory.save_message(":memory:", "session_A", "user", "msg1")
        
        # Add messages to session B
        memory.save_message(":memory:", "session_B", "user", "msg2")
        
        # Last session should be B
        self.assertEqual(memory.get_last_session(":memory:"), "session_B")

    def test_4_clear_session(self):
        """clear_session deletes only the target session."""
        memory.init_db(":memory:")
        
        session_a = "session_A"
        session_b = "session_B"
        
        memory.save_message(":memory:", session_a, "user", "keep me")
        memory.save_message(":memory:", session_b, "user", "delete me")
        memory.save_message(":memory:", session_b, "assistant", "delete me too")
        
        deleted_count = memory.clear_session(":memory:", session_b)
        
        self.assertEqual(deleted_count, 2)
        
        # Verify A is intact
        msgs_a = memory.load_session(":memory:", session_a)
        self.assertEqual(len(msgs_a), 1)
        self.assertEqual(msgs_a[0]["content"], "keep me")
        
        # Verify B is empty
        msgs_b = memory.load_session(":memory:", session_b)
        self.assertEqual(len(msgs_b), 0)

    def test_5_new_session_id(self):
        """new_session_id format."""
        import time
        id1 = memory.new_session_id()
        time.sleep(1) # Ensure time crosses a second boundary
        id2 = memory.new_session_id()
        
        self.assertTrue(id1.startswith("session_"))
        self.assertTrue(id2.startswith("session_"))
        self.assertEqual(len(id1), 23)  # len("session_YYYYMMDD_HHMMSS") = 8+8+1+6 = 23
        self.assertNotEqual(id1, id2)
