# PPTX Content Extraction & Template-Based Generation

This system automates the process of extracting content from a source PowerPoint file and rebuilding it using the most suitable template from a library of templates.

## Overall Approach (Reasoning Agent Architecture)
The system is divided into four main modular components, orchestrated by a **Reasoning Agent**:
1. **Content Extraction (`extractor.py`)**: Uses `python-pptx` to extract raw content. The **Reasoning Agent** then analyzes each slide to determine its **Intent** (e.g., "Strategy") and **Persona** (e.g., "The Roadmap Slide").
2. **Template Analysis (`analyzer.py`)**: Identifies available layouts and placeholders in potential templates.
3. **Agentic Evaluation (`evaluator.py` & `selector.py`)**: The agent performs a "design audit" to score templates based on semantic fit. It generates a **Reasoning Report** explaining why a template was chosen.
4. **Intelligent Generation (`generator.py`)**: Rebuilds the presentation using the agent's specific layout mapping and semantic categorization for each placeholder.

## Scoring Logic
The scoring system evaluates templates based on:
- **Layout Presence**: Higher points for templates having "Title Slide" and variety in layouts.
- **Placeholder Matching**: For each slide in the source, it checks if the template has a layout that can accommodate the required elements (titles, tables, text blocks).
- **Match Density**: The template that can most "naturally" fit the requested content receives the highest score.

## How to Run
1. Install dependencies:
   ```bash
   pip install python-pptx
   ```
2. Place your source file at `input/sample_input.pptx`.
3. Add your PowerPoint templates to the `templates/` directory.
4. Run the automated script:
   ```bash
   python main.py
   ```
5. Check the `output/` directory for the extracted JSON and the `final_presentation.pptx`.

## Libraries Used
- **python-pptx**: The core library for reading and writing `.pptx` files.
- **json**: For structured data storage.
- **os**: For file and directory management.
