import os
import json
from src.extractor import extract_content
from src.analyzer import analyze_template
from src.selector import select_best_template
from src.generator import generate_presentation
def main():
    input_pptx = "input/sample_input.pptx"
    templates_dir = "templates"
    output_dir = "output"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load environment variables for AI key
    from dotenv import load_dotenv
    load_dotenv()
    
    # Optional AI Agent
    ai_agent = None
    if os.getenv("GOOGLE_API_KEY"):
        try:
            from src.ai_agent import ReasoningAgent
            ai_agent = ReasoningAgent()
            print("AI Enhancement Enabled (Gemini 2.5 Flash).")
        except Exception as e:
            print(f"AI initialization failed: {e}")

    # 1. Extract
    print("--- 1. Extracting Content ---")
    content = extract_content(input_pptx)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(os.path.join(output_dir, "extracted_content.json"), "w") as f:
        json.dump(content, f, indent=4)
    print("Content extracted.")

    # 2. Analyze Templates
    print("\n--- 2. Analyzing Templates ---")
    template_files = [f for f in os.listdir(templates_dir) if f.endswith(".pptx")]
    if not template_files:
        print("No templates found in 'templates' directory.")
        # Fallback for demonstration if specific files exist
        if os.path.exists("input/sample_output.pptx"):
             template_files = ["sample_output.pptx"]
             templates_dir = "input"

    template_analyses = {}
    for t_file in template_files:
        t_path = os.path.join(templates_dir, t_file)
        print(f"Analyzing {t_file}...")
        template_analyses[t_file] = analyze_template(t_path)

    # 3. Select Best Template
    print("\n--- 3. Selecting Best Template ---")
    best_template_name, agent_result = select_best_template(content, template_analyses, ai_agent=ai_agent)
    print(f"Selected Template: {best_template_name}")
    
    if ai_agent:
        eval_info = agent_result["all_evaluations"].get(best_template_name, {})
        print(f"Reasoning: {eval_info.get('reasoning_report')}")

    with open(os.path.join(output_dir, "selected_template.txt"), "w") as f:
        f.write(best_template_name)

    # 4. Generate Final Presentation
    print("\n--- 4. Generating Final Presentation ---")
    best_template_path = os.path.join(templates_dir, best_template_name)
    output_path = os.path.join(output_dir, "final_presentation.pptx")
    generate_presentation(content, best_template_path, output_path, ai_agent=ai_agent, agent_result=agent_result)
    print("Done.")

if __name__ == "__main__":
    main()
