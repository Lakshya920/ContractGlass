import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import pdfplumber
import os
import json
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(
    page_title="ContractGlass | AI Risk Analyzer (Gemini)",
    page_icon="⚖️",
    layout="wide"
)

# 2. Initialize Gemini Client
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not api_key:
    st.error("🔑 Gemini API Key not found in Environment Variables! Please set GEMINI_API_KEY or GOOGLE_API_KEY.")
    st.stop()

# Updated initialization syntax for the latest google-genai library
client = genai.Client(api_key=api_key)

# 3. Define Structured JSON Output Schema using Pydantic
class RedFlag(BaseModel):
    clause_title: str = Field(description="Short, impactful name of the predatory/unfavorable clause found.")
    severity: str = Field(description="Must be either 'High' or 'Medium'.")
    original_text: str = Field(description="The exact word-for-word string from the contract that raised this flag.")
    plain_english: str = Field(description="A simplified translation explaining what this means to an average person.")
    counter_proposal: str = Field(description="A fair, rewritten version of this clause to send back to the client.")

class ContractAnalysisSchema(BaseModel):
    risk_score: int = Field(description="An integer from 0 (perfectly safe) to 100 (highly predatory).")
    summary: str = Field(description="A concise 2-sentence executive summary of the overall document safety.")
    red_flags: list[RedFlag] = Field(description="List of detected unfavorable clauses.")
    missing_items: list[str] = Field(description="Bullet points of standard client protections missing from this document.")

# 4. Mock Sample Documents
MOCK_CONTRACTS = {
    "Freelance / Contractor Agreement": (
        "INDEMNIFICATION & TERMINATION AGREEMENT\n\n"
        "The Client reserves the right to terminate this Agreement immediately at any time, for any reason or no reason, "
        "without prior notice and without penalty or further payment obligations to the Contractor. The Contractor shall "
        "remain fully bound to complete all transition services for a mandatory period of 120 days post-termination without "
        "additional compensation. Furthermore, the Contractor agrees to fully indemnify, defend, and hold harmless the Client "
        "from any and all claims, liabilities, losses, damages, or costs, including legal fees, arising out of "
        "any event whatsoever, regardless of fault or negligence by the Client. All intellectual property created under this "
        "agreement belongs immediately to the Client upon conception, irrespective of whether payments are delayed or entirely withheld."
    ),
    "Residential Lease": (
        "APARTMENT RENTAL LEASE AGREEMENT\n\n"
        "Landlord reserves the right to enter the premises at any hour of the day or night without prior notification to "
        "the Tenant for any inspection purpose. In the event that rent is delayed by more than 24 hours, a mandatory daily penalty "
        "compounding fee of 25% of the total monthly rent value will apply immediately. Tenant agrees that the security deposit is "
        "strictly non-refundable under any conditions, including clean structural vacancy upon standard lease expiration. Landlord "
        "is completely exempt from maintaining operational heating, plumbing, or electrical utility infrastructure during winter months."
    ),
    "Non-Disclosure Agreement (NDA)": (
        "MUTUAL NON-DISCLOSURE AND CONFIDENTIALITY DEED\n\n"
        "The Receiving Party agrees to maintain absolute secrecy regarding all disclosed operational mechanisms for an infinite "
        "and perpetual duration spanning beyond any termination dates. In the event of an alleged breach, the Disclosing Party "
        "shall be entitled to immediate injunctive relief along with liquidated damages fixed at a minimum of $5,000,000, without any "
        "requirement to prove actual financial damage or loss. The definition of Confidential Information shall broadly incorporate "
        "all public information, generalized market data, industry knowledge, and personal skills acquired by the employee prior to execution."
    )
}

# 5. Helper Functions
def extract_text_from_pdf(uploaded_file):
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def analyze_contract_with_gemini(contract_text, contract_type):
    prompt = f"""
    You are an elite corporate attorney specializing in protecting clients from predatory contracts.
    Analyze the provided contract text for a {contract_type}. 
    Identify hidden risks, predatory clauses, or missing legal protections.
    Extract the required attributes and format the output according to the requested schema.
    
    Here is the contract text:
    {contract_text}
    """
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ContractAnalysisSchema,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Gemini Analysis failed: {e}")
        return None

def generate_email_with_gemini(analysis_data, contract_type, recipient_name, tone):
    prompt = f"""
    You are a professional legal communications expert. Write an email to '{recipient_name}' regarding a '{contract_type}'.
    The email must politely but firmly ask to revise specific unfavorable clauses discovered during our review.
    Maintain a '{tone}' tone.
    
    Use these analysis findings:
    - Overall Risk Score Found: {analysis_data['risk_score']}/100
    - Micro Summary: {analysis_data['summary']}
    - Red Flags to mention politely: {[flag['clause_title'] for flag in analysis_data['red_flags']]}
    
    Output ONLY the raw string text of the email draft (Subject and Body). No preamble.
    """
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Failed to generate email draft automatically: {e}"

def generate_text_report(analysis, contract_type):
    report = f"===============================================\n"
    report += f"       CONTRACTGLASS RISK ANALYSIS REPORT       \n"
    report += f"===============================================\n\n"
    report += f"Contract Profile: {contract_type}\n"
    report += f"Aggregated Risk Score: {analysis['risk_score']}/100\n\n"
    report += f"EXECUTIVE SUMMARY:\n{analysis['summary']}\n\n"
    
    if analysis.get('missing_items'):
        report += f"MISSING PROTECTIVE ITEMS:\n"
        for item in analysis['missing_items']:
            report += f"- {item}\n"
        report += "\n"
        
    report += f"IDENTIFIED RED FLAGS:\n"
    for idx, flag in enumerate(analysis['red_flags'], 1):
        report += f"-----------------------------------------------\n"
        report += f"Risk #{idx}: {flag['clause_title']} [{flag['severity']} Severity]\n"
        report += f"Original text: \"{flag['original_text']}\"\n"
        report += f"Plain English: {flag['plain_english']}\n"
        report += f"Suggested Counter-Proposal:\n{flag['counter_proposal']}\n"
    return report

def draw_gauge(score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Overall Contract Risk Score", 'font': {'size': 18}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#1f1f1f"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#a3e635'},   # Safe (Green)
                {'range': [40, 70], 'color': '#fde047'},  # Warning (Yellow)
                {'range': [70, 100], 'color': '#ef4444'}  # Danger (Red)
            ]
        }
    ))
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=30, b=10))
    return fig

# 6. Streamlit User Interface Setup
st.title("⚖️ ContractGlass")
st.subheader("Expose hidden contract risks instantly using Google Gemini.")

# Initialize dynamic cross-session memory arrays safely
if "active_contract_text" not in st.session_state:
    st.session_state.active_contract_text = ""
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "previous_file_name" not in st.session_state:
    st.session_state.previous_file_name = None
if "email_draft" not in st.session_state:
    st.session_state.email_draft = None

# Sidebar Controls
st.sidebar.header("📁 Document Settings")
contract_type = st.sidebar.selectbox(
    "Select Contract Type",
    list(MOCK_CONTRACTS.keys()) + ["Custom Enterprise Agreement"]
)

uploaded_file = st.sidebar.file_uploader("Upload Contract (PDF Only)", type=["pdf"], key="file_input_widget")

st.sidebar.markdown("---")
st.sidebar.subheader("💡 Demo Quick-Load Contracts")
selected_demo = st.sidebar.selectbox("Choose a Predatory Scenario", list(MOCK_CONTRACTS.keys()))
use_demo = st.sidebar.button("✨ Load Selected Scenario")

# FIX 1: Smart File Input & Demo Toggle Handling
if use_demo:
    st.session_state.active_contract_text = MOCK_CONTRACTS[selected_demo]
    st.session_state.analysis_result = None
    st.session_state.email_draft = None
    st.session_state.previous_file_name = None
elif uploaded_file is not None and uploaded_file.name != st.session_state.previous_file_name:
    with st.spinner("Extracting text from PDF..."):
        extracted_text = extract_text_from_pdf(uploaded_file)
    if extracted_text:
        st.session_state.active_contract_text = extracted_text
        st.session_state.analysis_result = None
        st.session_state.email_draft = None
        st.session_state.previous_file_name = uploaded_file.name

# 6b. Main Content Area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 Contract Preview")
    if st.session_state.active_contract_text:
        st.text_area(
            "Document Content",
            st.session_state.active_contract_text,
            height=400,
            key="preview_area"
        )
        if st.button("🔍 Analyze Contract", type="primary", use_container_width=True):
            with st.spinner("Analyzing contract with Gemini... this may take a moment."):
                result = analyze_contract_with_gemini(st.session_state.active_contract_text, contract_type)
            if result:
                st.session_state.analysis_result = result
                st.session_state.email_draft = None
    else:
        st.info("👈 Upload a PDF or load a demo scenario from the sidebar to get started.")

with col2:
    st.subheader("📊 Risk Analysis")
    analysis = st.session_state.analysis_result
    if analysis:
        st.plotly_chart(draw_gauge(analysis["risk_score"]), use_container_width=True)
        st.markdown(f"**Executive Summary:** {analysis['summary']}")

        if analysis.get("missing_items"):
            st.markdown("**⚠️ Missing Protective Items**")
            for item in analysis["missing_items"]:
                st.markdown(f"- {item}")

        st.markdown("---")
        st.markdown("### 🚩 Red Flags")
        if analysis.get("red_flags"):
            for flag in analysis["red_flags"]:
                severity_icon = "🔴" if flag["severity"].lower() == "high" else "🟡"
                with st.expander(f"{severity_icon} {flag['clause_title']} ({flag['severity']})"):
                    st.markdown(f"**Original Text:**\n> {flag['original_text']}")
                    st.markdown(f"**Plain English:** {flag['plain_english']}")
                    st.markdown(f"**Suggested Counter-Proposal:**\n\n{flag['counter_proposal']}")
        else:
            st.success("No red flags detected in this document.")

        st.markdown("---")
        report_text = generate_text_report(analysis, contract_type)
        st.download_button(
            "⬇️ Download Full Report (.txt)",
            data=report_text,
            file_name="contractglass_report.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.info("Run an analysis to see the risk breakdown here.")

# 7. Email Draft Generator
st.markdown("---")
st.header("✉️ Draft a Revision Request Email")

if st.session_state.analysis_result:
    ecol1, ecol2, ecol3 = st.columns([2, 2, 1])
    with ecol1:
        recipient_name = st.text_input("Recipient Name", value="Client")
    with ecol2:
        tone = st.selectbox("Tone", ["Firm & Professional", "Friendly & Collaborative", "Formal & Assertive"])
    with ecol3:
        st.write("")
        st.write("")
        generate_email_clicked = st.button("Generate Draft", use_container_width=True)

    if generate_email_clicked:
        with st.spinner("Drafting email..."):
            st.session_state.email_draft = generate_email_with_gemini(
                st.session_state.analysis_result, contract_type, recipient_name, tone
            )

    if st.session_state.email_draft:
        st.text_area("Email Draft", st.session_state.email_draft, height=250)
        st.download_button(
            "⬇️ Download Email Draft (.txt)",
            data=st.session_state.email_draft,
            file_name="revision_request_email.txt",
            mime="text/plain"
        )
else:
    st.info("Analyze a contract first to generate a tailored revision request email.")