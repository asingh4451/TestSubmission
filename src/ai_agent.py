import os
import json
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

class ReasoningAgent:
    """
    The 'Brain' of the system. Handles semantic analysis, intent tagging, 
    and multi-step reasoning for template selection.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found. Please provide an API key.")
        
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)

    def analyze_slide_intent(self, slide_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phased Analysis:
        1. Extract semantic keywords.
        2. Identify slide 'persona' (e.g., 'The Strategy Slide', 'The Results Slide').
        3. Recommend design constraints (e.g., 'Requires high visual hierarchy').
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a senior presentation strategist. Analyze the following slide content and determine its core intent and psychological goal."),
            ("human", "Slide Content: {content}\n\nReturn a JSON with: 'intent', 'persona', 'key_takeaway', 'design_requirements'.")
        ])
        
        chain = prompt | self.llm
        try:
            # Focus only on text elements for intent analysis
            text_elements = [el.get('text_content') for el in slide_data.get('elements', []) if 'text_content' in el]
            simplified_content = {
                "title": slide_data.get('title'),
                "text": text_elements
            }
            
            response = chain.invoke({"content": json.dumps(simplified_content)})
            return self._parse_json(response.content)
        except Exception as e:
            print(f"Intent Analysis Error: {e}")
            return {"intent": "general info", "persona": "unknown"}

    def evaluate_template_fit(self, content_analysis: List[Dict], template_analysis: Dict) -> Dict[str, Any]:
        """
        Performs a 'Reasoning Run' to explain why a template fits.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Design Critic. Compare the source content structure with the template's available layouts."),
            ("human", """
            Content Analysis (By Slide): {content_analysis}
            Template Layouts: {layouts}
            
            Task:
            1. Evaluate how well this template can accommodate the specific intents.
            2. Assign a 'Fit Score' (0-100).
            3. Provide a 'Reasoning Report' explaining the score.
            4. CRITICAL: Create a 'layout_mapping' (dict of slide_idx -> layout_name). 
               Pick the layout_name that handles the most number of placeholders needed for that slide's intent.
            
            Return JSON with: 'score', 'reasoning_report', 'layout_mapping'.
            """)
        ])
        
        chain = prompt | self.llm
        try:
            response = chain.invoke({
                "content_analysis": json.dumps(content_analysis),
                "layouts": json.dumps(template_analysis.get('layouts', []))
            })
            return self._parse_json(response.content)
        except Exception as e:
            print(f"Template Evaluation Error: {e}")
            return {"score": 0, "reasoning_report": f"Error: {e}", "layout_mapping": {}}

    def optimize_content(self, slide_content: Dict, layout_info: Dict) -> Dict:
        """
        Intelligently maps slide content to template placeholders.
        Prevents clustering by distributing content across available placeholders.
        """
        system_prompt = (
            "You are a master presentation designer. Your task is to fit content into a template's specific placeholders. "
            "STRICT RULES:\n"
            "1. USE THE TEMPLATE: You must map content to the provided placeholder indices (idx).\n"
            "2. ANTI-CLUSTERING: Do not put all text in one placeholder if others are available.\n"
            "3. SEMANTIC MAPPING: Map 'Team' content to 'Team' placeholders, 'Results' to 'Charts/Data' placeholders, etc.\n"
            "4. NO OVERFLOW: If a placeholder is too small, summarize the content to fit."
        )
        
        user_prompt = f"""
        Source Slide Analysis: {json.dumps(slide_content, indent=2)}
        
        Target Layout: {layout_info.get('name')}
        Target Placeholders (idx, type, name): {json.dumps(layout_info.get('placeholders'), indent=2)}

        Task:
        - Return a JSON object where keys are the integer 'idx' of the placeholder and values are the content (string for text, or list of strings for bullets).
        - If the layout has multi-column placeholders, split the source bullet points between them.
        
        Return ONLY valid JSON.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ])

        chain = prompt | self.llm
        try:
            response = chain.invoke({})
            return self._parse_json(response.content)
        except Exception as e:
            print(f"Content Optimization Error: {e}")
            return {}

    def _parse_json(self, text: str) -> Dict:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text.strip())

# Global singleton or factory
def get_agent():
    return ReasoningAgent()
