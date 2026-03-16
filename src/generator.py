from pptx import Presentation
from pptx.util import Inches, Pt
import os

def generate_presentation(extracted_content, template_path, output_path, ai_agent=None, agent_result=None):
    """
    Generates a new PPTX using the template and extracted content.
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    prs = Presentation(template_path)
    layouts = {layout.name: layout for layout in prs.slide_layouts}
    
    # Default layouts
    title_layout = next((l for name, l in layouts.items() if "title" in name.lower() and "content" not in name.lower()), prs.slide_layouts[0])
    content_layout = next((l for name, l in layouts.items() if "content" in name.lower() or "text" in name.lower()), prs.slide_layouts[1])

    # Get layout mapping from agent if available
    layout_mapping = {}
    if agent_result and ai_agent:
        best_t_name = os.path.basename(template_path)
        # Try to find matching evaluation key
        eval_key = next((k for k in agent_result["all_evaluations"].keys() if k in best_t_name or best_t_name in k), None)
        if eval_key:
            layout_mapping = agent_result["all_evaluations"][eval_key].get("layout_mapping", {})

    for slide_data in extracted_content["slides"]:
        s_idx = str(slide_data["slide_index"])
        
        # 1. Try agent-provisioned mapping
        if s_idx in layout_mapping and layout_mapping[s_idx] in layouts:
            layout = layouts[layout_mapping[s_idx]]
        # 2. Heuristic fallback
        elif slide_data["slide_index"] == 1:
            layout = title_layout
        else:
            layout = content_layout

        print(f"Slide {slide_data['slide_index']}: Using layout '{layout.name}'")
        slide = prs.slides.add_slide(layout)
        
        # Set Title
        if slide_data.get("title") and slide.shapes.title:
            slide.shapes.title.text = slide_data["title"]
            
        # AI-Assisted Content Mapping
        if ai_agent:
            layout_info = {
                "name": layout.name,
                "placeholders": [{"idx": ph.placeholder_format.idx, "type": str(ph.placeholder_format.type), "name": ph.name} for ph in layout.placeholders]
            }
            mapping = ai_agent.optimize_content(slide_data, layout_info)
            
            for idx_str, content in mapping.items():
                try:
                    idx = int(idx_str)
                    ph = slide.placeholders[idx]
                    if isinstance(content, list):
                        tf = ph.text_frame
                        tf.clear()
                        for i, line in enumerate(content):
                            # ... (rest of paragraph logic)
                            p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
                            # Handle potential nested lists or strings
                            if isinstance(line, dict) and "text" in line:
                                p.text = line["text"]
                                p.level = line.get("level", 0)
                            else:
                                p.text = str(line)
                    else:
                        ph.text = str(content)
                except Exception as e:
                    print(f"Error applying AI mapping for placeholder {idx_str}: {e}")
            continue

        # Process elements (Default/Fallback)
        for element in slide_data["elements"]:
            # ... (rest of the existing logic)
            # This is a simplified mapper. Real-world mapping would be more complex.
            if "text_content" in element and element["text_content"]:
                # Try to find a body placeholder
                body_ph = None
                for ph in slide.placeholders:
                    if ph.placeholder_format.type in [2, 7]: # BODY or TEXT
                        # If there's already text, we might need a different placeholder or append
                        if not ph.text:
                            body_ph = ph
                            break
                
                if body_ph:
                    tf = body_ph.text_frame
                    tf.clear() # Clear default prompt
                    for i, para in enumerate(element["text_content"]):
                        p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
                        p.text = para["text"]
                        p.level = para["level"]
                else:
                    # Fallback: add a text box with dynamic positioning to avoid overlapping
                    idx_in_slide = slide_data["elements"].index(element)
                    left = Inches(1 + (idx_in_slide % 2))
                    top = Inches(2 + (idx_in_slide * 0.5))
                    width = Inches(4)
                    height = Inches(1)
                    txBox = slide.shapes.add_textbox(left, top, width, height)
                    tf = txBox.text_frame
                    for i, para in enumerate(element["text_content"]):
                        p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
                        p.text = para["text"]
                        p.level = para["level"]

            if "table_content" in element:
                rows = len(element["table_content"])
                cols = len(element["table_content"][0]) if rows > 0 else 0
                if rows > 0 and cols > 0:
                    left = Inches(1)
                    top = Inches(2)
                    width = Inches(8)
                    height = Inches(4)
                    table = slide.shapes.add_table(rows, cols, left, top, width, height).table
                    for r, row in enumerate(element["table_content"]):
                        for c, cell_text in enumerate(row):
                            table.cell(r, c).text = cell_text

    prs.save(output_path)
    print(f"Presentation generated at {output_path}")

if __name__ == "__main__":
    # Example usage (would be called by main.py)
    pass
