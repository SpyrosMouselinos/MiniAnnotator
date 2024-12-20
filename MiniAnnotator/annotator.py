import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime
import re
import yaml
from pathlib import Path

class TextAnnotator:
    """
    Main application class for the MiniAnnotator tool.
    Provides a GUI to load text, configure categories, annotate each sentence, and save progress.
    """
    def __init__(self, root):
        """
        Initialize the annotator, set up the main window, data structures, and GUI components.

        Args:
            root (tk.Tk): The main Tkinter window object.
        """
        self.root = root
        self.root.title("MiniAnnotator")
        self.root.geometry("1200x800")

        # Data storage
        self.sentences = []
        self.current_index = 0
        self.annotations = []
        
        # Initialize with empty category structure
        self.category_structure = {}
        
        # Track current selections
        self.current_selections = []
        
        self.setup_gui()

    def setup_gui(self):
        """
        Set up the GUI layout, including buttons for file operations, the text display area, 
        category frames, and navigation/confirmation controls.
        """
        # Top frame for file operations
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Button(top_frame, text="Load Configuration", command=self.load_configuration).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Load File", command=self.load_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Load Progress", command=self.load_progress).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Save Progress", command=self.save_annotations).pack(side=tk.LEFT, padx=5)

        # Text display frame
        text_frame = ttk.LabelFrame(self.root, text="Current Sentence", padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.text_display = ttk.Label(text_frame, wraplength=700)
        self.text_display.pack(fill=tk.BOTH, expand=True)

        # Bottom frame for navigation
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)
        
        self.confirm_button = ttk.Button(bottom_frame, text="Confirm", command=self.confirm_annotation, state=tk.DISABLED)
        self.confirm_button.pack(side=tk.RIGHT)

        # Progress label
        self.progress_label = ttk.Label(bottom_frame, text="Progress: 0/0")
        self.progress_label.pack(side=tk.BOTTOM)

        # Create main container for category levels
        self.category_frames = []
        self.create_category_level(0, list(self.category_structure.keys()))

    def create_category_level(self, level, options):
        """
        Creates a new frame of category buttons at the given level, 
        removing any deeper frames if they exist.

        Args:
            level (int): The depth level of the category structure (0-based).
            options (list): A list of categories or subcategories to create buttons for.
        """
        # Remove any existing frames for this level and deeper
        while len(self.category_frames) > level:
            frame = self.category_frames.pop()
            frame.destroy()

        # Create new frame for this level
        frame = ttk.LabelFrame(self.root, text=f"Level {level + 1}", padding="10")
        frame.pack(fill=tk.BOTH, padx=10, pady=5)
        self.category_frames.append(frame)

        # Create buttons for each option
        row = 0
        col = 0
        for option in options:
            # If option is a dictionary, get its key
            if isinstance(option, dict):
                display_text = list(option.keys())[0]
            else:
                display_text = option
                
            btn = ttk.Button(frame, text=display_text,
                             command=lambda o=display_text: self.select_category(level, o))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            col += 1
            if col > 4:  # 5 buttons per row
                col = 0
                row += 1

    def select_category(self, level, selection):
        """
        Handle a category selection at the given level, navigates deeper into the category structure,
        updates the current selections, and creates or removes category frames as needed.
        
        Args:
            level (int): The depth level of the category the user clicked.
            selection (str): The text/value the user selected.
        """
        # Update the path of selected categories
        self.current_selections = self.current_selections[:level] + [selection]

        # Traverse down from the root category structure based on the updated selections
        current_level = self.category_structure
        for sel in self.current_selections:
            if isinstance(current_level, dict) and sel in current_level:
                current_level = current_level[sel]
                if isinstance(current_level, dict) and 'types' in current_level:
                    current_level = current_level['types']
            elif isinstance(current_level, list):
                found_dict = False
                for item in current_level:
                    if isinstance(item, dict):
                        possible_key = list(item.keys())[0]
                        if possible_key == sel:
                            selected_value = item[sel]
                            if isinstance(selected_value, dict) and 'types' in selected_value:
                                current_level = selected_value['types']
                            else:
                                if 'types' in item:
                                    current_level = item['types']
                                else:
                                    current_level = selected_value
                            found_dict = True
                            break
                if not found_dict:
                    pass

        # Now act based on what 'current_level' is
        if isinstance(current_level, dict) and 'types' in current_level:
            self.create_category_level(level + 1, current_level['types'])
            return

        if isinstance(current_level, list):
            if selection in current_level:
                self.confirm_button.config(state=tk.NORMAL)
            else:
                self.create_category_level(level + 1, current_level)
            return

        self.confirm_button.config(state=tk.NORMAL)

    def load_file(self):
        """
        Allows the user to choose a text file, splits it into sentences, 
        and initializes the annotation state.
        """
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
                # Split by periods and newlines, clean up empty strings
                self.sentences = [s.strip() for s in re.split('[.\n]', text) if s.strip()]
                self.current_index = 0
                self.annotations = []
                self.update_display()

    def load_progress(self):
        """
        Allows the user to load previous annotations from a CSV and then select the matching 
        text file to compare. Loads and verifies the alignment between sentences and annotations.
        """
        # First, load the CSV file
        csv_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not csv_path:
            return

        try:
            # Load the annotations
            df = pd.read_csv(csv_path)
            
            # Now load the text file
            file_path = filedialog.askopenfilename(
                title="Select the original text file",
                filetypes=[("Text files", "*.txt")]
            )
            
            if not file_path:
                return

            # Load and split the text file
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
                new_sentences = [s.strip() for s in re.split('[.\n]', text) if s.strip()]

            # Convert DataFrame to list of dictionaries
            self.annotations = df.to_dict('records')

            # Verify the sentences match
            annotated_texts = [ann['text'] for ann in self.annotations]
            if not all(txt in new_sentences for txt in annotated_texts):
                messagebox.showerror(
                    "Error", 
                    "The selected text file doesn't match the annotations. Please start from scratch."
                )
                self.annotations = []
                return

            # Set up the current state
            self.sentences = new_sentences
            self.current_index = len(self.annotations)  # Start from where we left off
            
            # Update display
            self.update_display()
            messagebox.showinfo(
                "Progress Loaded", 
                f"Loaded {len(self.annotations)} previous annotations.\nContinuing from sentence {self.current_index + 1}"
            )

        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Failed to load progress: {str(e)}\nPlease start from scratch."
            )
            self.annotations = []
            self.current_index = 0

    def confirm_annotation(self):
        """
        Records the user's selected categories for the current sentence, appends to the annotation list, 
        advances to the next sentence, and resets the category selection frames.
        """
        if self.current_selections:
            # Get the full category path and final subcategory
            full_path = ' > '.join(self.current_selections)
            final_subcategory = self.current_selections[-1]
            
            self.annotations.append({
                'text': self.sentences[self.current_index],
                'categories': full_path,
                'final_subcategory': final_subcategory,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.current_index += 1
            self.update_display()
            
            # Clear current selections and remove category frames
            self.current_selections = []
            for frame in self.category_frames[1:]:
                frame.destroy()
            self.category_frames = self.category_frames[:1]
            
            self.confirm_button.config(state=tk.DISABLED)
            
            if self.current_index >= len(self.sentences):
                self.save_annotations()
                messagebox.showinfo("Complete", "Annotation complete! Results saved.")

    def update_display(self):
        """
        Updates the text display with the current sentence and progress information. 
        If no sentences remain, displays a completion or 'no text loaded' message.
        """
        if self.sentences and self.current_index < len(self.sentences):
            self.text_display.config(text=self.sentences[self.current_index])
            self.progress_label.config(text=f"Progress: {self.current_index + 1}/{len(self.sentences)}")
        else:
            self.text_display.config(text="No text loaded or annotation complete")

    def save_annotations(self):
        """
        Saves all annotations to a CSV file, appending a timestamp to the filename.
        """
        if self.annotations:
            df = pd.DataFrame(self.annotations)
            filename = f"annotations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            messagebox.showinfo("Saved", f"Annotations saved to {filename}")

    def load_configuration(self):
        """
        Loads a YAML configuration file, verifies that it has a 'categories' key, 
        and uses that to rebuild and display the category structure.
        """
        config_path = filedialog.askopenfilename(
            title="Select Configuration File",
            filetypes=[("YAML files", "*.yml *.yaml")]
        )
        
        if not config_path:
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            if 'categories' not in config:
                messagebox.showerror(
                    "Error", 
                    "Invalid configuration file: 'categories' key not found"
                )
                return
                
            self.category_structure = config['categories']
            
            # Clear existing category frames
            for frame in self.category_frames:
                frame.destroy()
            self.category_frames = []
            
            # Reset selections
            self.current_selections = []
            self.confirm_button.config(state=tk.DISABLED)
            
            # Create new category structure
            self.create_category_level(0, list(self.category_structure.keys()))
            
            messagebox.showinfo(
                "Success", 
                f"Configuration loaded successfully from {Path(config_path).name}"
            )
            
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Failed to load configuration: {str(e)}"
            )

def main():
    """
    Entry point of the application. Creates the main Tkinter 
    window and initializes the TextAnnotator GUI.
    """
    root = tk.Tk()
    app = TextAnnotator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
