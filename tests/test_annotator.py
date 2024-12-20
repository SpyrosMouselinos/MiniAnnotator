import os
import unittest
import tkinter as tk
from unittest import skipIf
from MiniAnnotator.annotator import TextAnnotator

# This condition checks if we're missing a DISPLAY variable (on Linux)
# and if we're not on Windows. (Windows doesn't need DISPLAY.)
SKIP_GUI = (os.environ.get("DISPLAY") is None) and (os.name != "nt")

@skipIf(SKIP_GUI, "Skipping GUI tests due to no display environment in headless mode.")
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
        # Close the Tk window to be safe
        root.destroy()

    # Add more tests as desired...

if __name__ == "__main__":
    unittest.main() 