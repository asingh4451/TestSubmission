import streamlit as st
import os
import json
import tempfile
from src.extractor import extract_content
from src.analyzer import analyze_template
from src.selector import select_best_template
from src.generator import generate_presentation

# ── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title="AI PPT Builder",
    page_icon="🎨",
    layout="centered",
)

# ── Custom styles ────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    /* Selective font application to avoid breaking icons */
    html, body, .stMarkdown, .stButton, .stSelectbox, .stMultiSelect, .stFileUploader, p, h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
    }

    /* Hide broken Material Symbol text aliases that sometimes leak */
    .material-symbols-rounded {
        font-size: 0 !important;
        line-height: 0 !important;
        display: none !important;
    }

    .block-container {
        max-width: 820px;
        padding-top: 2rem;
    }

    /* Header gradient */
    .app-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #9333ea 100%);
        padding: 2.2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }
    .app-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: white !important;
    }
    .app-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
        color: white !important;
    }

    /* Info card */
    .info-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ───────────────────────────────────────────────
st.markdown(
    """
    <div class="app-header">
        <h1>🎨 AI PPT Builder</h1>
        <p>Transform content into beautiful presentations instantly</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Main UI ──────────────────────────────────────────────
st.markdown("### 📤 Upload Your Content")
uploaded_file = st.file_uploader("Choose a source PPTX file", type="pptx")

st.divider()

# ── AI Settings ──────────────────────────────────────────
st.markdown("### 🤖 AI Enhancement")
with st.container():
    col1, col2 = st.columns([1, 2])
    with col1:
        use_ai = st.toggle("Enable AI Optimization", value=False, help="Use Gemini to intelligently map content to placeholders and suggest layouts.")
    
    with col2:
        if use_ai:
            api_key = st.text_input("Google API Key", type="password", value=os.getenv("GOOGLE_API_KEY", ""), help="Required for AI features. Get one at [aistudio.google.com](https://aistudio.google.com/)")
            if api_key:
                os.environ["GOOGLE_API_KEY"] = api_key

st.divider()

st.markdown("### 🛠️ Templates")
templates_dir = "templates"
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

template_files = [f for f in os.listdir(templates_dir) if f.endswith(".pptx")]

if not template_files:
    st.warning("No templates found in the 'templates/' directory. Please add some .pptx files.")
else:
    selected_templates = st.multiselect(
        "Select templates to consider (or leave empty to use all)",
        template_files,
        default=template_files
    )

    if st.button("🚀 Generate Presentation", type="primary", use_container_width=True):
        if not uploaded_file:
            st.error("Please upload a source PPTX file first.")
        elif use_ai and not os.getenv("GOOGLE_API_KEY"):
            st.error("Please provide a Google API Key to use AI features.")
        else:
            with st.status("🏗️ Processing...", expanded=True) as status:
                # Create temp directory
                with tempfile.TemporaryDirectory() as tmp_dir:
                    # Save uploaded file
                    source_path = os.path.join(tmp_dir, "source.pptx")
                    with open(source_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Initialize AI Agent if requested
                    ai_agent = None
                    if use_ai:
                        try:
                            from src.ai_agent import ReasoningAgent
                            ai_agent = ReasoningAgent()
                            st.write("🤖 Reasoning Agent ready (Gemini 2.5 Flash).")
                        except Exception as e:
                            st.error(f"Failed to initialize AI: {e}")
                            st.stop()

                    # 1. Extract
                    st.write("🔍 Extracting content...")
                    content = extract_content(source_path)
                    
                    # 2. Analyze Templates
                    st.write("📊 Analyzing templates...")
                    template_analyses = {}
                    for t_file in selected_templates:
                        t_path = os.path.join(templates_dir, t_file)
                        template_analyses[t_file] = analyze_template(t_path)
                    
                    # 3. Select
                    st.write("🎯 Selecting best template (Agentic Evaluation)...")
                    best_template_name, agent_result = select_best_template(content, template_analyses, ai_agent=ai_agent)
                    st.success(f"Selected best match: **{best_template_name}**")
                    
                    # Display Reasoning
                    if use_ai and agent_result:
                        with st.expander("🧠 Agent Reasoning Report"):
                            eval_info = next((v for k, v in agent_result["all_evaluations"].items() if k == best_template_name), {})
                            st.markdown(f"**Score:** {eval_info.get('score', 0)}/100")
                            st.info(eval_info.get('reasoning_report', "No report generated."))
                            
                            st.markdown("### 🧬 Slide Intents")
                            for intent in agent_result.get("slide_intents", []):
                                st.write(f"**Slide {intent['slide_index']}:** {intent['persona']}")
                                st.caption(f"Intent: {intent['intent']}")

                    # 4. Generate
                    st.write("✨ Rebuilding presentation...")
                    output_path = os.path.join(tmp_dir, "final_presentation.pptx")
                    best_template_path = os.path.join(templates_dir, best_template_name)
                    generate_presentation(content, best_template_path, output_path, ai_agent=ai_agent, agent_result=agent_result)
                    
                    status.update(label="✅ Generation Complete!", state="complete")
                    
                    # Provide download link
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Final Presentation",
                            data=f,
                            file_name="final_presentation.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True
                        )

st.divider()
with st.expander("ℹ️ How it works"):
    st.markdown("""
    1. **Extraction**: We analyze your source PPTX to extract all text, bullets, and tables.
    2. **Analysis**: We look at available templates to understand their layouts and placeholders.
    3. **Scoring**: We match your content needs to the template capabilities to find the perfect fit.
    4. **Generation**: We rebuild the presentation slide-by-slide in the new style.
    """)
