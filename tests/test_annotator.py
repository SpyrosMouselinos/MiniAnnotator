import unittest
import tkinter as tk
from MiniAnnotator.annotator import TextAnnotator

class TestAnnotator(unittest.TestCase):
    """
    Simple test class for TextAnnotator to ensure
    it initializes correctly and basic methods run without error.
    """
    def test_initial_state(self):
        """
        Ensure TextAnnotator initializes with zero current_index and empty structures.
        """
        root = tk.Tk()
        app = TextAnnotator(root)
        self.assertEqual(app.current_index, 0)
        self.assertEqual(len(app.sentences), 0)
        self.assertEqual(len(app.annotations), 0)

    # Add more tests as desired...

if __name__ == "__main__":
    unittest.main() 