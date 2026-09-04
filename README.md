# ⚖️ ContractGlass

> Expose hidden contract risks instantly using Google Gemini.

ContractGlass is an AI-driven legal document auditor designed to protect contractors, freelancers, and tenants from one-sided, predatory agreements. By parsing contract text or uploaded PDF agreements, ContractGlass scores legal risks, translates confusing legalese into plain English, and provides fair counter-proposals.

### 🌟 Key Features

* **Interactive Risk Gauge:** Visualizes document safety on a calibrated 0–100 risk scale powered by Plotly[cite: 4].
* **Red Flag Detection:** Extracts predatory clauses word-for-word, assigns severity levels (High/Medium), and suggests equitable revisions[cite: 4].
* **Missing Clause Audit:** Flags critical missing standard protections such as grace periods, mutual indemnification, and clear termination notice[cite: 4].
* **Revision Email Generator:** Drafts formal, firm, or collaborative revision request emails ready to send back to the client or counterparty[cite: 4].
* **Built-in Demo Scenarios:** Test instant analysis on simulated predatory contractor agreements, residential leases, and NDAs[cite: 4].
* **Report Export:** Download structured executive summary reports as plain text files[cite: 4].

### 🛠️ Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io/)[cite: 4]
* **AI Engine:** Google Gemini (`gemini-3.6-flash`) via `google-genai`[cite: 4]
* **Schema Validation:** [Pydantic](https://docs.pydantic.dev/) structured JSON generation[cite: 4]
* **Document Parsing:** [pdfplumber](https://github.com/jsvine/pdfplumber)[cite: 4]
* **Data Visualization:** [Plotly](https://plotly.com/python/)[cite: 4]
