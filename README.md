# 🎙️ Impact Application AI

## From a Voice Note to a Fundable Proposal

**AI Builder Hackathon — Challenge 1**

Impact Application AI is an AI-powered application assistant that transforms an applicant's **voice note, business documents, and supporting photos** into a structured funding application.

Instead of requiring a small-business owner to manually complete a long application form, the AI agent extracts available information, identifies missing information, asks targeted follow-up questions, validates the answers, and prepares a completed application for submission.

---

## 🚀 Problem

Many small-business owners have the information needed for a funding application but struggle with:

* Long and complicated application forms
* Limited digital literacy
* Language barriers
* Remembering every required field
* Translating a spoken business story into formal application responses
* Providing accurate business and financial information

The goal is to let an applicant simply **tell their story** and allow the AI agent to guide them through the remaining requirements.

---

## 💡 Solution

Impact Application AI transforms:

**🎤 Voice Note + 📄 Business Licence + 📸 Business Photos**

into:

**📋 A complete and validated funding application**

### Core Workflow

```text
Applicant
   │
   ├── Voice Note
   ├── Business Licence
   └── Workshop / Business Photo
           │
           ▼
   ┌────────────────────┐
   │   AI Processing    │
   └─────────┬──────────┘
             │
             ▼
      Speech-to-Text
             │
             ▼
       Information
        Extraction
             │
             ▼
     Application State
             │
             ▼
    Missing Information?
          /       \
        Yes        No
         │          │
         ▼          ▼
    Follow-up    Validation
    Questions        │
         │           │
         └─────┬─────┘
               ▼
        Applicant Review
               │
               ▼
       Application Ready
               │
               ▼
       Jotform Submission
```

---

# ✨ Key Features

## 🎤 Multilingual Voice Transcription

The system supports voice input in:

* English
* Amharic
* Afaan Oromo

Gemini is used to convert the applicant's voice note into text and to support
multilingual extraction and follow-up processing.

---

## 🧠 AI Information Extraction

The extraction agent identifies information explicitly provided by the applicant.

Example:

```json
{
  "company_name": "Almaz Spice Mill",
  "registration_number": "12345/2020",
  "address": "Bekoji Tera",
  "years_in_operation": 5,
  "employees_current": 8,
  "female_employees_current": 6,
  "sales_current": "1.5 million birr"
}
```

The system follows an evidence-based approach:

* Never invent information
* Never guess missing values
* Preserve applicant-provided information
* Distinguish current values from historical values
* Mark missing information explicitly
* Track the source of extracted information

---

# 📄 Document Evidence

Applicants can provide supporting documents such as:

* Business licences
* Registration documents
* Workshop/business photographs

Document information can be incorporated as additional evidence alongside the voice transcript.

The system distinguishes between:

```text
Voice evidence
Document evidence
Applicant-provided follow-up
```

This helps prevent unsupported claims from being inserted into an application.

---

# 💬 Agentic Follow-Up Interview

The agent does not stop after the first extraction.

If required information is missing, it asks the applicant targeted questions.

Example:

```text
Agent:
What is your business registration number?

Applicant:
12345/2020

Agent:
How many employees do you currently have?

Applicant:
Eight.

Agent:
What are your current annual sales?

Applicant:
Approximately 1.5 million birr.
```

Each answer is added to the application state.

The process continues until the required application information is complete.

---

# 🔄 Iterative Application Completion

The application is treated as a continuously updated state.

```text
Extract
   ↓
Check missing fields
   ↓
Ask question
   ↓
Receive answer
   ↓
Update application
   ↓
Check again
   ↓
Ask next question
   ↓
...
   ↓
Complete
```

The agent does not ask questions for information it already has.

If an applicant provides multiple pieces of information in a single response, the system extracts all of them before deciding what to ask next.

---

# 🛡️ Evidence-First Design

The system follows a core principle:

> **If the applicant did not provide the information, the AI should not invent it.**

For example, if the applicant says:

> "We have about 10 employees."

The system preserves the approximate nature of the statement rather than silently converting it into an exact value.

If the applicant never provides their registration number:

```json
{
  "registration_number": {
    "value": null,
    "status": "missing"
  }
}
```

The agent asks the applicant instead of guessing.

---

# 📊 Application State

Each extracted field contains structured information such as:

```json
{
  "value": "Almaz Spice Mill",
  "status": "established",
  "source": "voice_note",
  "confidence": 0.95,
  "note": "Explicitly extracted from applicant voice transcript."
}
```

Possible states include:

* `established`
* `unverified`
* `missing`

Possible sources include:

* `voice_note`
* `document`
* `applicant`
* `reviewed`

---

# 🏗️ Architecture

```text
                    ┌──────────────────┐
                    │     Applicant    │
                    └────────┬─────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
             Voice        Licence      Photo
                │            │            │
                └────────────┼────────────┘
                             ▼
                  ┌────────────────────┐
                  │   Evidence Layer   │
                  └─────────┬──────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │   Transcription    │
                  └─────────┬──────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │  AI Extraction     │
                  └─────────┬──────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │ Application State  │
                  └─────────┬──────────┘
                            │
                            ▼
                  ┌────────────────────┐
                  │ Completeness Check │
                  └─────────┬──────────┘
                            │
                       Missing?
                       /         \
                     Yes          No
                      │            │
                      ▼            ▼
                ┌──────────┐ ┌──────────┐
                │ Interview│ │Validation│
                │   Agent  │ │          │
                └────┬─────┘ └────┬─────┘
                     │             │
                     └──────┬──────┘
                            ▼
                     Applicant Review
                            │
                            ▼
                    Jotform / Output
```

---

# 🧰 Technology Stack

### Frontend

* Python
* Streamlit

### AI

* Google Gemini via the `google-genai` SDK
* Gemini Flash for speech-to-text and structured extraction
* Gemini multimodal vision for licence and business-photo evidence
* Gemini preview TTS for spoken follow-up questions

### Processing

* Python
* JSON
* Regular expressions
* `python-dotenv`

### Application Integration

* Jotform integration helpers are available for form synchronization

---

# 📁 Project Structure

```text
impact-application-ai/
│
├── app.py
│
├── agents/
│   ├── __init__.py
│   ├── ai_agents.py
│   ├── form_integration.py
│   ├── gemini_extraction_agent.py
│   ├── google_speech_agent.py
│   ├── groq_agent.py
│   └── voice_followup_agent.py
│
├── models/
│   └── schema.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key
```

If Jotform API integration is enabled:

```env
JOTFORM_API_KEY=your_jotform_api_key
```

### ⚠️ Security

Never commit `.env` to GitHub.

Add the following to `.gitignore`:

```text
.env
.venv/
__pycache__/
*.pyc
```

---

# ▶️ Running the Application

Start Streamlit:

```bash
streamlit run app.py
```

The application will normally be available at:

```text
http://localhost:8501
```

---

# 🧪 Testing

Run the test suite with:

```bash
pytest
```

For development, you can also use the application's mock transcript option
instead of uploading an audio file.

Example:

```text
My name is Almaz Wolde. I run Almaz Spice Mill in Bekoji Tera.
The business has operated for five years.
We currently have eight employees, six of whom are women.
Our annual sales are approximately 1.5 million birr.
We need grinding and packaging equipment.
```

The system should:

1. Extract the available information.
2. Populate the application.
3. Identify missing information.
4. Ask follow-up questions.
5. Update the application with the answers.
6. Repeat until the required information is complete.
7. Validate the completed application.
8. Prepare it for submission.

---

# 🔁 Example Agent Interaction

### Initial Input

> "I run a spice processing business in Bekoji. We have been operating for five years and have eight employees."

### Extracted Information

```text
Business type       ✓
Address             ✓
Years operating     ✓
Employees           ✓

Registration number ✗
Annual sales        ✗
Ownership           ✗
Market information  ✗
Equipment needs     ✗
...
```

### Agent

> What is your business registration number?

### Applicant

> 12345/2020.

### Agent

> What are your current annual sales?

### Applicant

> Around 1.5 million birr.

The agent continues until the required application information is complete.

---

# 🔍 Validation

Before submission, the application should be checked for:

## Missing Information

```text
registration_number = missing
```

## Contradictions

```text
Earlier: 8 employees
Later: 12 employees
```

The agent should ask:

> You previously mentioned 8 employees, but later mentioned 12. Which number represents your current employees?

## Unsupported Claims

The system should never create values that were not provided by:

* The applicant
* A supporting document
* A verified source

---

# 🌍 Multilingual Design

The applicant can communicate naturally in supported languages:

```text
English
Amharic
Afaan Oromo
```

The system is designed to preserve the original evidence while allowing the application workflow to operate across languages.

This is especially important for applicants who are more comfortable explaining their businesses verbally than completing written forms.

---

# 🤖 Why This Is Agentic

Impact Application AI is not simply a chatbot or document extractor.

The agent:

### 1. Perceives

Understands:

* Speech
* Images
* Documents
* Applicant responses

### 2. Extracts

Converts unstructured information into structured application data.

### 3. Reasons

Determines:

* What information is available
* What information is missing
* What needs clarification
* Whether information conflicts

### 4. Plans

Dynamically decides which follow-up question should be asked next.

### 5. Maintains State

Remembers the application's current values throughout the interaction.

### 6. Validates

Checks for:

* Missing fields
* Contradictions
* Unsupported claims
* Invalid or ambiguous information

### 7. Acts

Prepares and, when Jotform API access is available, submits the completed application.

---

# 🎯 Hackathon Impact

The system aims to reduce the barrier between **having a business story** and **having a fundable application**.

Instead of forcing applicants to understand complex digital forms, the applicant can simply explain their business naturally.

The AI handles the complexity of:

```text
Speech
  ↓
Understanding
  ↓
Extraction
  ↓
Questioning
  ↓
Validation
  ↓
Application completion
  ↓
Submission
```

The applicant remains in control of the information and can review the final application before submission.

---

# 🚧 Current Limitations

* Jotform API integration requires a valid Jotform account and API credentials.
* Exact Jotform field IDs must be mapped before automated API submission.
* Document evidence requires appropriate OCR/vision processing.
* AI-generated extraction should remain reviewable by the applicant.
* Internet connectivity is required for cloud AI services.
* API availability and rate limits depend on the external services being used.

---

# 🔮 Future Improvements

* Full Jotform API submission
* Automatic Jotform field discovery and mapping
* Voice-based follow-up conversations
* Real-time multilingual voice interaction
* Stronger document verification
* Evidence conflict resolution
* Applicant identity verification
* Funding-readiness scoring
* Human reviewer dashboard
* Persistent application history
* Integration with additional funding platforms

---

# 👥 Intended Users

The primary users are:

* Micro and small business owners
* Entrepreneurs applying for funding
* Applicants with limited digital literacy
* Applicants who prefer voice-based communication
* Organizations processing large numbers of funding applications

---

# 📜 Principle

> **The AI assists the applicant; it does not fabricate the applicant.**

Every application should be based on information that can be traced to:

1. The applicant's own statement.
2. Supporting documents.
3. Explicit follow-up answers.
4. Applicant review and confirmation.

---

## 🏆 AI Builder Hackathon

**Challenge 1 — Applicant Path**

**From a Voice Note to a Fundable Proposal**

Built as an AI agent that helps transform an applicant's real-world business story into a complete, evidence-based funding application.
