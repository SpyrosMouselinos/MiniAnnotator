# MiniAnnotator

MiniAnnotator is a lightweight text annotation tool that allows users to categorize sentences from text files using a simple graphical interface. It supports multiple hierarchical levels of categories defined in a YAML configuration file.

## Features

- Load and process text files (.txt)
- Automatic sentence splitting (by periods or newlines)
- Dynamic hierarchical annotation system:
  - Configurable categories and subcategories via YAML
  - Support for multiple category levels
  - Easy to modify category structure
- User-friendly GUI interface
- Progress tracking
- Save/Load functionality:
  - Export annotations to CSV format
  - Resume previous annotation sessions
  - Automatic progress saving
- Windows executable available

## Installation

1. Install required dependencies (e.g., PyYAML, pandas, tkinter)
2. Download or clone the source code from this repository (or use the Windows executable from the releases if available)
3. Run the application with:
   ```bash
   python annotator.py
   ```

## Configuration

The category structure is defined in a YAML file. You can create your own configuration file with any number of hierarchical levels. MiniAnnotator will read each level and generate category buttons accordingly.

### Basic Structure

Below is an example that shows how categories, subcategories, and final selection items can be nested:

```yaml
categories:
  Category1:
    types:
      SubCategory1:
        types:
          - FinalType1
          - FinalType2
      SubCategory2:
        types:
          - FinalType3
          - FinalType4
  Category2:
    types:
      SubCategory3:
        types:
          - FinalType5
          - FinalType6
```

Note the nested dictionaries:
- Category1 → types → SubCategory1, SubCategory2
- SubCategory1 → types → [FinalType1, FinalType2]

Each branch can have its own "types" key, which itself can be a list of either strings (final categories) or dictionaries (more nestable subcategories).

### YAML Example for Extended Hierarchies

If you have many levels, each subcategory you want to expand further must be a dictionary, like so:

```yaml
categories:
  Task-Focused Exchange:
    types:
      - Asks Questions (Closed-ended):
          types:
            - Medical Condition
            - Therapeutic Regimen
            - Lifestyle Information
            - Psychosocial Information
            - Other Information
      - Asks Questions (Open-ended):
          types:
            - Medical Condition
            - Therapeutic Regimen
            - Lifestyle Information
            - Psychosocial Information
            - Other Information
```

### Tips and Best Practices for Config

- Always start with "categories:" at the root
- Maintain consistent indentation to ensure YAML validity
- Use "types:" for nested levels
- Each entry in a "types:" list can be:
  - A string (final category, no more expansion)
  - A dictionary with one key (the subcategory name) mapped to another dict that has a "types" key
- Avoid special characters in category names

## Usage

1. Launch the application:
   ```bash
   python annotator.py
   ```

2. Click the "Load Configuration" button and select your YAML file for annotation categories
   - Ensure your file follows the hierarchical "categories → types" structure described above

3. Click "Load File" to open your text file (.txt) for annotation. The tool will automatically split the text into sentences

4. MiniAnnotator then displays:
   - The current sentence
   - Category buttons at Level 1 (the top-level categories)

5. When you click a category button:
   - MiniAnnotator shows subcategories at the next level (if any)
   - Continue clicking until you reach a final category (a simple string with no deeper "types")

6. Click "Confirm" to:
   - Save the annotation for the current sentence
   - Move on to the next sentence

7. Click "Save Progress" at any time to write out your annotations (plus timestamps) to a CSV file

8. To pause and resume later:
   - Use "Save Progress" to export your current annotations to CSV
   - Later, use "Load Progress" to import that CSV, then select the original text file
   - The tool will pick up where you left off

## Example Workflow

1. Open MiniAnnotator → "Load Configuration" → Select "my_config.yml"
2. The main window updates to reflect the top-level categories from "my_config.yml"
3. Click "Load File" → Choose "my_text.txt"
4. The first sentence appears. You click through Category1 → SubCategory1 → FinalType1
5. Click "Confirm." You advance to the next sentence
6. At any time, click "Save Progress" to record your annotations to CSV
7. If you close and reopen MiniAnnotator, "Load Progress" lets you resume from your CSV and the same text file

## Output Format

The tool generates a CSV file with columns:
- text: The original sentence
- categories: The joined path (e.g., "Category1 > SubCategory1 > FinalType1")
- final_subcategory: The last selected category name (e.g., "FinalType1")
- timestamp: Date and time when you confirmed the annotation

Example CSV output:
```csv
text,categories,final_subcategory,timestamp
"The Earth revolves around the Sun.",Method > Quantitative > Statistical,Statistical,2024-03-20 14:30:45
"I believe AI will change everything.",Result > Finding > Unexpected,Unexpected,2024-03-20 14:31:02
```

## License

MIT License

## Contributing

Contributions are *not welcome!* I am doing this for my girlfriend's project.
