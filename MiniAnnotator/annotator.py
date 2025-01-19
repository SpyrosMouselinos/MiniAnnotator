import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime
import re
import yaml
from pathlib import Path
import urllib.request  # Standard library way to download a file over HTTP
import json
import webbrowser

__version__ = "1.0.2"  # Current version of MiniAnnotator

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
        self.root.title(f"MiniAnnotator v{__version__}")  # Add version to window title
        self.root.geometry("1200x800")
        self.root.resizable(True, True)

        # -- Apply a ttk Style --
        style = ttk.Style(self.root)
        # Try "clam", "alt", "default", "classic", or other built-in themes
        style.theme_use("clam")

        # Example style customizations (adjust to your preference):
        style.configure(
            "TButton",
            font=("Segoe UI", 10),
            padding=6
        )
        style.configure(
            "TLabel",
            font=("Segoe UI", 10),
            padding=4
        )
        style.configure(
            "TLabelframe",
            font=("Segoe UI", 10, "bold"),
            foreground="#333333"
        )
        style.configure(
            "TLabelframe.Label",
            foreground="#333333"
        )
        style.configure(
            "TFrame",
            background="#f0f0f0"  # May not be honored on all themes/OSs
        )

        # Data storage
        self.sentences = []
        self.current_index = 0
        self.annotations = []

        # Track the user's chosen split method: "nl" for newlines or "fs" for full stops
        self.split_method = None

        # Initialize with empty category structure
        self.category_structure = {}

        # Track current selections
        self.current_selections = []

        # Add new instance variables to track skipped indices
        self.skipped_indices = []
        self.processing_skips = False
        self.skip_index = 0

        # Add observation window size variable
        self.observation_window = tk.IntVar(value=1)

        self.setup_gui()

        # Initial button states:
        # 1) Only "Load Configuration" is enabled at app start.
        # 2) Everything else is disabled until the user successfully loads a config.
        self.load_config_button.config(state="normal")
        self.load_file_button.config(state="disabled")
        self.load_progress_button.config(state="disabled")
        self.save_progress_button.config(state="disabled")

    def setup_gui(self):
        """
        Set up the GUI layout, including buttons for file operations, the text display area,
        category frames, and navigation/confirmation controls.
        """
        # Top frame for file operations
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        # Left side - buttons
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side=tk.LEFT)

        self.load_config_button = ttk.Button(button_frame, text="Load Configuration", command=self.load_configuration)
        self.load_config_button.pack(side=tk.LEFT)

        self.load_file_button = ttk.Button(button_frame, text="Load File", command=self.load_file)
        self.load_file_button.pack(side=tk.LEFT, padx=5)

        self.load_progress_button = ttk.Button(button_frame, text="Load Progress", command=self.load_progress)
        self.load_progress_button.pack(side=tk.LEFT, padx=5)

        self.save_progress_button = ttk.Button(button_frame, text="Save Progress", command=self.save_annotations)
        self.save_progress_button.pack(side=tk.LEFT, padx=5)

        self.download_stuffz_button = ttk.Button(button_frame, text="Download Stuffz", command=self.download_stuffz)
        self.download_stuffz_button.pack(side=tk.LEFT, padx=5)

        # Add Check Updates button
        self.check_updates_button = ttk.Button(button_frame, text="Check Updates", command=self.check_updates)
        self.check_updates_button.pack(side=tk.LEFT, padx=5)

        # Right side - slider
        slider_frame = ttk.Frame(top_frame)
        slider_frame.pack(side=tk.RIGHT, padx=20)

        ttk.Label(slider_frame, text="Lines observation window:").pack(side=tk.LEFT)
        self.window_slider = ttk.Scale(
            slider_frame,
            from_=1,
            to=5,
            orient=tk.HORIZONTAL,
            variable=self.observation_window,
            command=lambda v: self.on_slider_change(round(float(v))),
            value=1
        )
        self.window_slider.pack(side=tk.LEFT, padx=5)
        
        # Add label to show current value
        self.window_value_label = ttk.Label(slider_frame, text="1")
        self.window_value_label.pack(side=tk.LEFT, padx=5)

        # Text display frame with context panels
        text_frame = ttk.LabelFrame(self.root, text="Text Context", padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Previous lines panel
        prev_frame = ttk.LabelFrame(text_frame, text="Previous Lines", padding="5")
        prev_frame.pack(fill=tk.X, padx=5, pady=2)
        self.prev_display = ttk.Label(prev_frame, wraplength=700, foreground="gray")
        self.prev_display.pack(fill=tk.X)

        # Current line panel
        current_frame = ttk.LabelFrame(text_frame, text="Current Line", padding="5")
        current_frame.pack(fill=tk.X, padx=5, pady=2)
        self.text_display = ttk.Label(current_frame, wraplength=700, font=("Segoe UI", 10, "bold"))
        self.text_display.pack(fill=tk.X)

        # Next lines panel
        next_frame = ttk.LabelFrame(text_frame, text="Next Lines", padding="5")
        next_frame.pack(fill=tk.X, padx=5, pady=2)
        self.next_display = ttk.Label(next_frame, wraplength=700, foreground="gray")
        self.next_display.pack(fill=tk.X)

        # Bottom frame for navigation
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)

        # "Skip" button (always enabled)
        self.skip_button = ttk.Button(bottom_frame, text="Skip", command=self.skip_annotation)
        self.skip_button.pack(side=tk.RIGHT, padx=(0,5))

        self.confirm_button = ttk.Button(bottom_frame, text="Confirm", command=self.confirm_annotation, state=tk.DISABLED)
        self.confirm_button.pack(side=tk.RIGHT)

        # Progress label
        self.progress_label = ttk.Label(bottom_frame, text="Progress: 0/0")
        self.progress_label.pack(side=tk.BOTTOM)

        # Create main container for category levels
        self.category_frames = []
        self.create_category_level(0, list(self.category_structure.keys()))

    def download_stuffz(self):
        """
        Always enabled button to download configuration.yml from the public GitHub repo.
        1) Asks the user to pick a folder. 
        2) Fetches configuration.yml from the MiniAnnotator GitHub repository (raw). 
        3) Saves the file into the chosen folder.
        
        This is simpler than a full git clone or running 'wget' commands,
        and only retrieves the single file needed.
        """
        target_dir = filedialog.askdirectory(title="Choose Where to Save configuration.yml")
        if not target_dir:
            return  # user canceled

        url = "https://raw.githubusercontent.com/SpyrosMouselinos/MiniAnnotator/main/configuration.yml"
        destination_path = Path(target_dir) / "configuration.yml"

        try:
            urllib.request.urlretrieve(url, destination_path)
            messagebox.showinfo("Download Complete", f"Saved to: {destination_path}")
        except Exception as e:
            messagebox.showerror("Download Failed", f"Something went wrong:\n{str(e)}")

    def choose_split_method(self):
        """
        Pops up a small dialog allowing the user to choose whether to split
        the loaded text by newlines or by full stops.
        """
        choice_var = tk.StringVar(value="nl")
        win = tk.Toplevel(self.root)
        win.title("Choose Split Method")
        win.grab_set()

        ttk.Label(win, text="How would you like to split the text?").pack(pady=5)
        ttk.Radiobutton(win, text="Split by Newlines", variable=choice_var, value="nl").pack(anchor="w")
        ttk.Radiobutton(win, text="Split by Full Stops", variable=choice_var, value="fs").pack(anchor="w")

        def confirm_choice():
            self.split_method = choice_var.get()
            win.destroy()

        ttk.Button(win, text="OK", command=confirm_choice).pack(pady=5)
        self.root.wait_window(win)

    def load_file(self):
        """
        Allows the user to choose a text file, pops up a choice of splitting by newlines or full stops,
        then splits the file into sentences accordingly and initializes the annotation state.
        """
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not file_path:
            return

        self.choose_split_method()

        if self.split_method not in ("nl", "fs"):
            messagebox.showwarning("No Split Chosen", "No valid split method selected. Using default (newlines).")
            self.split_method = "nl"

        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

            if self.split_method == "fs":
                # Split by full stops
                self.sentences = [s.strip() for s in re.split(r'\.', text) if s.strip()]
            else:
                # Default to splitting by newlines
                self.sentences = [s.strip() for s in text.split('\n') if s.strip()]

        self.current_index = 0
        self.annotations = []
        self.update_display()

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
                messagebox.showerror("Error", "Invalid configuration file: 'categories' key not found")
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

            # Once a config is loaded, disable load configuration and enable load file & load progress
            self.load_config_button.config(state="disabled")
            self.load_file_button.config(state="normal")
            self.load_progress_button.config(state="normal")
            # Keep save button disabled until at least one annotation is done

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to load configuration: {str(e)}"
            )

    def create_category_level(self, level, options):
        """
        Creates a new frame of category buttons at the given level,
        replacing any existing frames.

        Args:
            level (int): The depth level of the category structure (0-based).
            options (list): A list of categories or subcategories to create buttons for.
        """
        # Remove any existing category frame
        if self.category_frames:
            self.category_frames[0].destroy()
            self.category_frames = []

        frame = ttk.LabelFrame(self.root, text=f"Level {level + 1}", padding="10")
        frame.pack(fill=tk.BOTH, padx=10, pady=5)
        self.category_frames = [frame]  # Keep only one frame

        row, col = 0, 0
        
        # Add Back button for all levels except the first
        if level > 0:
            back_btn = ttk.Button(
                frame,
                text="← Back",
                command=lambda: self.go_back(level)
            )
            back_btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            col += 1
            if col > 4:  # 5 buttons per row
                col = 0
                row += 1

        for option in options:
            if isinstance(option, dict):
                display_text = list(option.keys())[0]
            else:
                display_text = option

            btn = ttk.Button(
                frame,
                text=display_text,
                command=lambda o=display_text: self.select_category(level, o)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

            col += 1
            if col > 4:  # 5 buttons per row
                col = 0
                row += 1

    def go_back(self, current_level):
        """
        Handles going back one level in the category hierarchy.
        
        Args:
            current_level (int): The current level we're going back from
        """
        # Remove the current level's selection
        self.current_selections.pop()
        
        # If we have previous selections, rebuild from the parent level
        if self.current_selections:
            # Start from top
            current_level = self.category_structure
            # Traverse to the correct level
            for sel in self.current_selections:
                current_level = self._drill_down(current_level, sel)
            # Create the parent level's options
            self.create_category_level(len(self.current_selections), current_level)
        else:
            # If no selections left, go back to root level
            self.create_category_level(0, list(self.category_structure.keys()))
        
        self.confirm_button.config(state=tk.DISABLED)

    def _drill_down(self, current_level, selection):
        if isinstance(current_level, dict):
            # For example: {"Socio-emotional Exchange": {"types": [...]}, "Task-Focused Exchange": {...}}
            if selection in current_level:
                value = current_level[selection]
                if isinstance(value, dict) and "types" in value:
                    return value["types"]
                if isinstance(value, list):
                    return value
                return None

        if isinstance(current_level, list):
            for item in current_level:
                if isinstance(item, dict):
                    # e.g. {"Asks Questions (Closed-ended)": {"types": [...]} }
                    key = list(item.keys())[0]
                    if key == selection:
                        subvalue = item[key]
                        if isinstance(subvalue, dict) and "types" in subvalue:
                            return subvalue["types"]
                        elif isinstance(subvalue, list):
                            return subvalue
                        else:
                            return None
                elif isinstance(item, str):
                    if item == selection:
                        # It's a leaf string
                        return None
        return None

    def select_category(self, level, selection):
        # Truncate or extend self.current_selections
        self.current_selections = self.current_selections[:level] + [selection]

        # Start from top
        current_level = self.category_structure

        # Traverse each already-chosen selection
        for sel in self.current_selections:
            next_level = self._drill_down(current_level, sel)
            if next_level is None:
                current_level = None
                break
            else:
                current_level = next_level

        # If current_level is None, we have no further sub-level => leaf
        if current_level is None:
            self.confirm_button.config(state=tk.NORMAL)
            # Remove frames deeper than 'level'
            while len(self.category_frames) > level + 1:
                self.category_frames.pop().destroy()
            return
        else:
            # Deeper sub-level exists
            while len(self.category_frames) > level + 1:
                self.category_frames.pop().destroy()
            self.create_category_level(level + 1, current_level)
            self.confirm_button.config(state=tk.DISABLED)

    def load_progress(self):
        """
        Allows the user to load previous annotations from a CSV and then select the matching
        text file to compare. Loads and verifies the alignment between sentences and annotations.
        """
        csv_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not csv_path:
            return

        try:
            df = pd.read_csv(csv_path)

            file_path = filedialog.askopenfilename(
                title="Select the original text file",
                filetypes=[("Text files", "*.txt")]
            )
            if not file_path:
                return

            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()

            if not self.split_method:
                self.choose_split_method()

            if self.split_method == "fs":
                new_sentences = [s.strip() for s in re.split(r'\.', text) if s.strip()]
            else:
                new_sentences = [s.strip() for s in text.split('\n') if s.strip()]

            # Convert the entire CSV into a list of dict records
            all_records = df.to_dict('records')

            # Validate that all annotated texts so far are in new_sentences
            annotated_texts = [ann['text'] for ann in all_records]
            if not all(txt in new_sentences for txt in annotated_texts):
                messagebox.showerror(
                    "Error",
                    "The selected text file doesn't match the annotations. Please start from scratch."
                )
                self.annotations = []
                return

            self.sentences = new_sentences

            # Separate records into completed and skipped
            completed_records = [r for r in all_records if r['final_subcategory'] != 'SKIP']
            skip_records = [r for r in all_records if r['final_subcategory'] == 'SKIP']

            if skip_records:
                # Load all completed records
                self.annotations = completed_records
                
                # Create a list of indices for skipped items
                self.skipped_indices = [self.sentences.index(r['text']) for r in skip_records]
                self.skipped_indices.sort()  # Ensure they're in order
                self.processing_skips = True
                self.skip_index = 0
                
                # Set current_index to the first skip
                self.current_index = self.skipped_indices[0]

                messagebox.showinfo(
                    "Progress Loaded",
                    f"Loaded {len(completed_records)} completed annotations.\n"
                    f"Found {len(skip_records)} skipped items to review.\n"
                    f"Resuming from first skipped sentence at position {self.current_index + 1}."
                )
            else:
                # No skips found - load all records and continue from where we left off
                self.annotations = all_records
                self.current_index = len(self.annotations)
                self.processing_skips = False
                messagebox.showinfo(
                    "Progress Loaded",
                    f"Loaded {len(self.annotations)} previous annotations.\n"
                    f"Continuing from sentence {self.current_index + 1}"
                )

            self.update_display()

            # If we have at least one annotation, disable 'Load File' & 'Load Progress'
            # and enable 'Save Progress'
            if len(self.annotations) > 0:
                self.load_file_button.config(state="disabled")
                self.load_progress_button.config(state="disabled")
                self.save_progress_button.config(state="normal")

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to load progress: {str(e)}\nPlease start from scratch."
            )
            self.annotations = []
            self.current_index = 0

    def confirm_annotation(self):
        """
        Records the user's selected categories for the current sentence and advances to next.
        """
        if self.current_selections:
            full_path = ' > '.join(self.current_selections)
            final_subcategory = self.current_selections[-1]

            self.annotations.append({
                'text': self.sentences[self.current_index],
                'categories': full_path,
                'final_subcategory': final_subcategory,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # Handle progression differently if we're processing skips
            if self.processing_skips:
                self.skip_index += 1
                if self.skip_index < len(self.skipped_indices):
                    self.current_index = self.skipped_indices[self.skip_index]
                else:
                    # We've finished processing all skips, move to the first unannotated sentence
                    self.processing_skips = False
                    annotated_texts = {ann['text'] for ann in self.annotations}
                    for i, sentence in enumerate(self.sentences):
                        if sentence not in annotated_texts:
                            self.current_index = i
                            break
                    else:
                        # If no unannotated sentences found, we're done
                        self.current_index = len(self.sentences)
            else:
                self.current_index += 1

            self.update_display()

            # Clear deeper frames and selections
            self.current_selections = []
            for frame in self.category_frames[1:]:
                frame.destroy()
            self.category_frames = self.category_frames[:1]

            self.confirm_button.config(state=tk.DISABLED)

            if self.current_index >= len(self.sentences):
                self.save_annotations()
                messagebox.showinfo("Complete", "Annotation complete! Results saved.")
            else:
                # If this is the first annotation made, we disable "Load File" and "Load Progress"
                # and enable "Save Progress"
                if len(self.annotations) == 1:
                    self.load_file_button.config(state="disabled")
                    self.load_progress_button.config(state="disabled")
                    self.save_progress_button.config(state="normal")

    def on_slider_change(self, value):
        """
        Handler for slider value changes. Updates the display with new context window.
        """
        value = round(float(value))  # Ensure we have an integer
        self.observation_window.set(value)  # Update the variable
        self.window_value_label.config(text=str(value))  # Update the displayed value
        self.update_display()

    def update_display(self):
        """
        Updates all three text displays with the previous, current, and next sentences.
        Shows multiple context lines based on the observation window setting.
        """
        if not self.sentences:
            self.prev_display.config(text="")
            self.text_display.config(text="No text loaded")
            self.next_display.config(text="")
            self.progress_label.config(text="Progress: 0/0")
            return

        if self.current_index >= len(self.sentences):
            self.prev_display.config(text="")
            self.text_display.config(text="Annotation complete")
            self.next_display.config(text="")
            return

        window_size = self.observation_window.get()

        # Update previous lines
        prev_lines = []
        start_idx = max(0, self.current_index - window_size)
        if start_idx == 0 and self.current_index > 0:
            prev_lines.append("(Start of document)")
        for i in range(start_idx, self.current_index):
            prev_lines.append(self.sentences[i])
        self.prev_display.config(text="\n\n".join(prev_lines) if prev_lines else "(No previous lines)")

        # Update current line
        self.text_display.config(text=self.sentences[self.current_index])

        # Update next lines
        next_lines = []
        end_idx = min(len(self.sentences), self.current_index + window_size + 1)
        for i in range(self.current_index + 1, end_idx):
            next_lines.append(self.sentences[i])
        if end_idx >= len(self.sentences) and self.current_index < len(self.sentences) - 1:
            next_lines.append("(End of document)")
        self.next_display.config(text="\n\n".join(next_lines) if next_lines else "(No next lines)")

        # Update progress label
        self.progress_label.config(text=f"Progress: {self.current_index + 1}/{len(self.sentences)}")

    def save_annotations(self):
        """
        Saves all annotations to a CSV file, appending a timestamp and suffix to the filename
        depending on the chosen split method (defaulting to 'nl' if unset).
        """
        if self.annotations:
            df = pd.DataFrame(self.annotations)

            if not self.split_method:
                self.split_method = 'nl'

            suffix = f"_{self.split_method}"
            filename = f"annotations{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)

            messagebox.showinfo("Saved", f"Annotations saved to {filename}")

    def skip_annotation(self):
        """
        Marks the current sentence as SKIP and moves on to the next one.
        """
        self.annotations.append({
            'text': self.sentences[self.current_index],
            'categories': 'SKIP',
            'final_subcategory': 'SKIP',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Handle progression differently if we're processing skips
        if self.processing_skips:
            self.skip_index += 1
            if self.skip_index < len(self.skipped_indices):
                self.current_index = self.skipped_indices[self.skip_index]
            else:
                # We've finished processing all skips, move to the first unannotated sentence
                self.processing_skips = False
                annotated_texts = {ann['text'] for ann in self.annotations}
                for i, sentence in enumerate(self.sentences):
                    if sentence not in annotated_texts:
                        self.current_index = i
                        break
                else:
                    # If no unannotated sentences found, we're done
                    self.current_index = len(self.sentences)
        else:
            self.current_index += 1

        self.update_display()

        # Reset deeper frames and selections
        for frame in self.category_frames[1:]:
            frame.destroy()
        self.category_frames = self.category_frames[:1]
        self.current_selections = []

        # If this is the very first annotation (even if 'SKIP'), disable load & enable save
        if len(self.annotations) == 1:
            self.load_file_button.config(state="disabled")
            self.load_progress_button.config(state="disabled")
            self.save_progress_button.config(state="normal")

        if self.current_index >= len(self.sentences):
            self.save_annotations()
            messagebox.showinfo("Complete", "Annotation complete! Results saved.")

    def check_updates(self):
        """
        Checks GitHub tags for newer versions and prompts the user if an update is available.
        """
        try:
            # GitHub API URL for tags
            url = "https://api.github.com/repos/SpyrosMouselinos/MiniAnnotator/tags"
            
            # Make request to GitHub API
            req = urllib.request.Request(url)
            req.add_header('Accept', 'application/vnd.github.v3+json')
            
            with urllib.request.urlopen(req) as response:
                tags = json.loads(response.read())
            
            if not tags:
                messagebox.showinfo("Update Check", "No releases found.")
                return
                
            # Get latest version from tags (removing 'v' prefix)
            latest_version = tags[0]['name'].lstrip('v')
            
            # Compare versions (simple string comparison since we use semantic versioning)
            if latest_version > __version__:
                if messagebox.askyesno(
                    "Update Available",
                    f"A new version (v{latest_version}) is available!\n"
                    f"Current version: v{__version__}\n\n"
                    "Would you like to visit the download page?"
                ):
                    webbrowser.open("https://github.com/SpyrosMouselinos/MiniAnnotator/tags")
            else:
                messagebox.showinfo(
                    "Up to Date",
                    f"You are running the latest version (v{__version__})!"
                )
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to check for updates: {str(e)}"
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
