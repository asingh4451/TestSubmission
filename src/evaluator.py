from typing import List, Dict, Any
from .ai_agent import ReasoningAgent

class Evaluator:
    """
    Coordinates the comparison between content and templates.
    """
    def __init__(self, agent: ReasoningAgent):
        self.agent = agent

    def perform_full_evaluation(self, extracted_content: Dict, template_analyses: Dict[str, Dict]) -> Dict[str, Any]:
        """
        The multi-step process:
        1. Analyze intent for all slides.
        2. Evaluate each template against those intents.
        3. Determine the absolute best fit.
        """
        # Step 1: Deep Content Analysis
        print("Agent is analyzing slide intents...")
        slide_intents = []
        for slide in extracted_content.get("slides", []):
            intent = self.agent.analyze_slide_intent(slide)
            intent['slide_index'] = slide.get('slide_index')
            slide_intents.append(intent)

        # Step 2: Comparative Template Evaluation
        evaluations = {}
        for t_name, t_analysis in template_analyses.items():
            print(f"Agent is evaluating template: {t_name}...")
            eval_result = self.agent.evaluate_template_fit(slide_intents, t_analysis)
            evaluations[t_name] = eval_result

        # Step 3: Global Selection
        best_template = max(evaluations.items(), key=lambda x: x[1].get('score', 0))[0]
        
        return {
            "best_template": best_template,
            "slide_intents": slide_intents,
            "all_evaluations": evaluations
        }
