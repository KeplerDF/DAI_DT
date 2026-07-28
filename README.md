# DAI_DT — Debate Analytics Dashboard & Evaluation API

> **Dan's Artificial Intelligence Debate Trial (DAI_DT)**  
> An AI-powered full-stack application that extracts, evaluates, and scores debate transcripts from YouTube using structured Google Gemini models and Next.js analytics visualizations.

---

## 📌 Project Overview

**DAI_DT** allows users to paste any YouTube debate URL, automatically extract its formatted timestamped transcript, and send it through an objective, mathematical scoring framework powered by **Google Gemini**.

### Key Features
- **YouTube Transcript Extraction:** Automatically parses video captions and timestamps.
- **Objective Mathematical Scoring:** Quantifies debate performance based on logical rigor:
  - **Logical Points ($L$):** $+3.0$ pts *(Claim + Warrant + Impact)*
  - **Unrebutted Hits ($U$):** $+2.0$ pts *(Unanswered valid logic)*
  - **Logical Fallacies ($F$):** $-2.0$ pts *(Strawman, Ad Hominem, etc.)*
  - **Insinuations ($I$):** $-1.5$ pts *(Bad-faith rhetoric / loaded statements)*
  - **Net Score Formula:** $\text{Net Score} = (L \times 3) + (U \times 2) - (F \times 2) - (I \times 1.5)$
  - **Integrity Ratio:** $\text{Integrity Ratio} = \left( \frac{L}{L + F + I} \right) \times 100\%$
- **Interactive Web Dashboard:** Clean Next.js dashboard featuring metrics cards, talk-time breakdown graphs, and a complete transcript ledger itemizing every score change.
- **Local Caching & Database:** Caches evaluated debates in a local SQLite database using SQLModel to prevent redundant API calls.

---

## 🛠 Tech Stack

### Frontend (`/debate-frontend`)
- **Framework:** Next.js 16 (App Router, React 19, TypeScript)
- **Styling:** Tailwind CSS
- **Icons & Charts:** Lucide-React, Recharts
- **HTTP Client:** Axios

### Backend (`/`)
- **Framework:** FastAPI (Python 3.10+)
- **ORM & Database:** SQLModel / SQLite
- **LLM Engine:** Google GenAI SDK (`gemini-flash-latest` model)
- **Environment Management:** `python-dotenv`

---

## 🚀 Local Setup & Installation

Follow these steps to clone, configure, and run both the backend and frontend locally on your machine.

---

### Prerequisites
Make sure you have the following installed on your system:
- [Node.js](https://nodejs.org/) (v18 or higher)
- [Python](https://www.python.org/) (v3.10 or higher)
- Git
- A **Google Gemini API Key** (Get one for free at [Google AI Studio](https://aistudio.google.com/))

---

### 1. Clone the Repository

```bash
git clone [https://github.com/keplerdf/DAI_DT.git](https://github.com/keplerdf/DAI_DT.git)
cd DAI_DT
```

---

### 2. Backend Setup (FastAPI)

1. **Create and activate a Python virtual environment:**

   *On Windows (Git Bash/PowerShell):*
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # In PowerShell: .venv\Scripts\Activate.ps1
   ```

   *On macOS / Linux:*
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Python dependencies:**
   ```bash
   pip install fastapi uvicorn sqlmodel google-genai python-dotenv pydantic
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the project **root directory** (`DAI_DT/.env`):

   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Start the FastAPI Backend Server:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

   The backend API will start at: `http://localhost:8000`  
   *You can view the interactive OpenAPI documentation at `http://localhost:8000/docs`.*

---

### 3. Frontend Setup (Next.js)

1. **Navigate to the frontend directory:**
   ```bash
   cd debate-frontend
   ```

2. **Install Node modules:**
   ```bash
   npm install
   ```

3. **Configure Local Next.js API Route:**
   Ensure `debate-frontend/app/api/analyze/route.ts` points to your **local backend** (`http://localhost:8000/analyze-debate`):

   ```typescript
   // In debate-frontend/app/api/analyze/route.ts
   const renderResponse = await axios.post('http://localhost:8000/analyze-debate', {
     youtube_url: url,
     transcript_text: formattedTranscript,
   });
   ```

4. **Start the Next.js Development Server:**
   ```bash
   npm run dev
   ```

5. **Open the App:**  
   Navigate to `http://localhost:3000` in your web browser.

---

## 📋 How to Use

1. Copy any public **YouTube debate or discussion URL** (e.g., `https://www.youtube.com/watch?v=pb9VfCG7_XU`).
2. Paste the link into the **Debate Analytics Dashboard** input bar.
3. Click **Analyze**.
4. Watch real-time status updates as the transcript is parsed and passed to the Gemini model.
5. Review the generated analytics:
   - **Speaker Breakdown:** Net Scores, Integrity Ratios, and Talk Times.
   - **Transcript Ledger:** Chronological breakdown with timestamps, quotes, categorization, and logical impact descriptions.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).