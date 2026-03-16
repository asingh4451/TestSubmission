def score_template(content_summary, template_analysis):
    """
    Scores a template based on how well its layouts match the content requirements.
    """
    score = 0
    # content_summary could be a dict with counts of types: titles, tables, two-column etc.
    
    # 1. Check if it has a Title Slide layout
    has_title_slide = any("title" in l["name"].lower() and "content" not in l["name"].lower() for l in template_analysis["layouts"])
    if has_title_slide:
        score += 10
        
    # 2. Check for layout variety
    score += len(template_analysis["layouts"]) * 2
    
    # 3. Check for specific content types expected in content_summary
    for slide in content_summary.get("slides", []):
        needed_types = []
        if slide.get("title"): needed_types.append("TITLE")
        has_table = any("table_content" in el for el in slide.get("elements", []))
        if has_table: needed_types.append("TABLE")
        
        # Simple heuristic: find if any layout supports these
        # This is a very basic scoring, can be refined
        match_found = False
        for layout in template_analysis["layouts"]:
            placeholder_types = [ph["type"] for ph in layout["placeholders"]]
            if all(t in str(placeholder_types) for t in needed_types):
                match_found = True
                break
        if match_found:
            score += 5

    return score

from .evaluator import Evaluator

def select_best_template(source_content, template_analyses, ai_agent=None):
    """
    If AI Agent is provided, use the Reasoning Evaluator.
    Otherwise, fallback to heuristic scoring.
    """
    if ai_agent:
        evaluator = Evaluator(ai_agent)
        result = evaluator.perform_full_evaluation(source_content, template_analyses)
        return result["best_template"], result
    
    # Heuristic Fallback
    best_template = None
    best_score = -1
    for template_name, analysis in template_analyses.items():
        score = score_template(source_content, analysis)
        if score > best_score:
            best_score = score
            best_template = template_name
            
    return best_template, {"best_template": best_template, "all_evaluations": {best_template: {"score": best_score, "reasoning_report": "Heuristic selection", "layout_mapping": {}}}}
