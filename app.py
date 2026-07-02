import streamlit as st
import google.generativeai as genai
import json
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Newsletter Generator",
    page_icon="📰",
    layout="wide"
)

st.title("📰 AI Newsletter Generator")
st.markdown("Generate complete, ready-to-send "
            "newsletters from a topic using Gemini.")
st.markdown("---")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    api_key = st.sidebar.text_input(
        "Gemini API Key:",
        type="password",
        placeholder="Get free key at aistudio.google.com"
    )

HISTORY_FILE = "newsletter_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(data):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(data, f, indent=2)

if 'history' not in st.session_state:
    st.session_state.history = load_history()

NEWSLETTER_TYPES = {
    "Tech & AI Update":
        "weekly technology and AI news roundup",
    "Startup/Business":
        "startup news, funding rounds and business insights",
    "Personal Brand":
        "personal/professional update from an individual",
    "Product Launch":
        "announcement of a new product or feature",
    "Educational/How-To":
        "educational content teaching a skill or concept",
    "Community Digest":
        "community updates, events and highlights",
    "College Club Update":
        "college club or society activity update"
}

TONES = [
    "Professional & Polished",
    "Casual & Friendly",
    "Witty & Energetic",
    "Inspirational",
    "Concise & Data-Driven"
]

def generate_newsletter(
    topic, news_type, tone, audience,
    sections, cta, length, api_key
):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""You are an expert newsletter 
copywriter who writes high-engagement newsletters.

Write a complete newsletter with these specs:

Topic: {topic}
Type: {NEWSLETTER_TYPES[news_type]}
Tone: {tone}
Target Audience: {audience}
Number of content sections: {sections}
Call to action: {cta}
Length: {length}

Structure the newsletter with:
1. A catchy subject line (under 60 characters)
2. A preview text (under 100 characters)
3. An engaging opening hook (2-3 sentences)
4. {sections} distinct content sections, each with
   a bold header and 2-4 sentences of content
5. A closing paragraph
6. A clear call-to-action: {cta}
7. A sign-off

Make it genuinely engaging, specific and not generic.
Use real-sounding details where helpful (the user 
can edit specifics later).

Format your response as JSON:
{{
  "subject_line": "...",
  "preview_text": "...",
  "opening_hook": "...",
  "sections": [
    {{"header": "...", "content": "..."}}
  ],
  "closing": "...",
  "cta_text": "...",
  "signoff": "..."
}}

Return ONLY valid JSON, no markdown."""

    response = model.generate_content(prompt)
    return response.text

def parse_response(text):
    try:
        clean = text.strip()
        if clean.startswith('```'):
            lines = clean.split('\n')
            clean = '\n'.join(lines[1:-1])
        return json.loads(clean)
    except:
        return None

def render_newsletter_text(result):
    lines = []
    lines.append(f"Subject: {result['subject_line']}")
    lines.append(f"Preview: {result['preview_text']}")
    lines.append("")
    lines.append(result['opening_hook'])
    lines.append("")
    for sec in result['sections']:
        lines.append(f"## {sec['header']}")
        lines.append(sec['content'])
        lines.append("")
    lines.append(result['closing'])
    lines.append("")
    lines.append(f"👉 {result['cta_text']}")
    lines.append("")
    lines.append(result['signoff'])
    return "\n".join(lines)

# Tabs
tab1, tab2, tab3 = st.tabs([
    "✨ Generate Newsletter",
    "📚 History",
    "💡 Best Practices"
])

with tab1:
    st.markdown("### ✨ Newsletter Details")

    col1, col2 = st.columns(2)

    with col1:
        topic = st.text_area(
            "Newsletter topic:",
            placeholder="e.g. This week's biggest "
                        "AI launches and what they "
                        "mean for developers",
            height=100
        )
        news_type = st.selectbox(
            "Newsletter type:",
            list(NEWSLETTER_TYPES.keys()))
        tone = st.selectbox("Tone:", TONES)

    with col2:
        audience = st.text_input(
            "Target audience:",
            placeholder="e.g. CS students interested "
                        "in ML and internships")
        sections = st.slider(
            "Number of content sections:", 2, 6, 3)
        length = st.selectbox(
            "Length:",
            ["Short (quick read)",
             "Medium (standard newsletter)",
             "Long (in-depth)"])
        cta = st.text_input(
            "Call-to-action goal:",
            placeholder="e.g. Reply with your "
                        "thoughts / Check out my "
                        "latest project")

    if not api_key:
        st.warning(
            "Enter your Gemini API key in the "
            "sidebar to generate newsletters!")
    else:
        if st.button("✨ Generate Newsletter",
                     type="primary",
                     use_container_width=True):
            if topic.strip():
                with st.spinner(
                    "🤖 Writing your newsletter..."
                ):
                    raw = generate_newsletter(
                        topic, news_type, tone,
                        audience or "general readers",
                        sections, cta or
                        "Reply and let me know "
                        "your thoughts",
                        length, api_key)
                    result = parse_response(raw)

                if result:
                    st.markdown("---")
                    st.markdown("### 📧 Your Newsletter")

                    st.text_input(
                        "📌 Subject Line:",
                        value=result['subject_line'])
                    st.text_input(
                        "👁️ Preview Text:",
                        value=result['preview_text'])

                    full_text = render_newsletter_text(
                        result)
                    st.text_area(
                        "📝 Full Newsletter (editable):",
                        value=full_text,
                        height=500)

                    st.download_button(
                        "⬇️ Download as .txt",
                        full_text,
                        "newsletter.txt",
                        "text/plain")

                    st.session_state.history.append({
                        'timestamp': str(datetime.now()),
                        'topic': topic,
                        'type': news_type,
                        'subject': result['subject_line'],
                        'full_text': full_text
                    })
                    save_history(
                        st.session_state.history)
                    st.success("✅ Saved to history!")
                else:
                    st.error(
                        "Could not parse response. "
                        "Try again!")
            else:
                st.warning("Please enter a topic!")

with tab2:
    st.markdown("### 📚 Newsletter History")
    if not st.session_state.history:
        st.info("No newsletters generated yet!")
    else:
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            save_history([])
            st.rerun()
        for entry in reversed(st.session_state.history):
            with st.expander(
                f"📰 {entry['subject'][:50]} — "
                f"{entry['timestamp'][:16]}"
            ):
                st.markdown(f"**Type:** {entry['type']}")
                st.markdown(f"**Topic:** {entry['topic']}")
                st.text_area(
                    "Content:", value=entry['full_text'],
                    height=300,
                    key=f"hist_{entry['timestamp']}")

with tab3:
    st.markdown("### 💡 Newsletter Best Practices")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        #### 📌 Subject Lines
        - Under 60 characters
        - Create curiosity, avoid clickbait
        - Numbers and specifics perform well
        - Avoid spam trigger words (FREE, !!!)

        #### 🎯 Structure
        - Hook in the first 2 sentences
        - One clear idea per section
        - Short paragraphs (2-4 sentences)
        - Single, clear call-to-action
        """)
    with col2:
        st.markdown("""
        #### 📊 Sending Tips
        - Tuesday–Thursday mornings perform best
        - Consistency matters more than frequency
        - Always include a way to reply/engage
        - Test subject lines with small audiences

        #### ✅ Before You Send
        - Read it out loud once
        - Check all links work
        - Verify facts and figures
        - Get one other person to proofread
        """)

st.markdown("---")
st.markdown(
    "Built by **Jyotiraditya** | "
    "AI Newsletter Generator | "
    "Powered by Google Gemini"
)