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
