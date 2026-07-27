# DAI_DT = Dan's Artificial Intelligence Debate Trial

import os
import re
import random
from typing import List
from contextlib import asynccontextmanager
from fastapi import HTTPException, status, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv
from sqlmodel import Session, select
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)
from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig

from database import engine, create_db_and_tables, get_session
from models import Debate

load_dotenv()  # Loads environment variables from .env


# -------------------------------------------------------------------
# FastAPI Lifespan (Creates database table on startup)
# -------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Debate Evaluation API",
    description="Extracts YouTube transcripts and generates an objective debate evaluation using Gemini.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://keplerdf.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini Client (uses GEMINI_API_KEY from environment)
ai_client = genai.Client()


# -------------------------------------------------------------------
# Pydantic Schemas for Request and Structured Response
# -------------------------------------------------------------------

class DebateRequest(BaseModel):
    youtube_url: str = Field(
        ...,
        example="https://www.youtube.com/watch?v=pb9VfCG7_XU",
        description="Full YouTube URL or video ID."
    )


class SpeakerMetrics(BaseModel):
    logical_points_L: int = Field(..., description="Count of valid logical points (Claim + Warrant + Impact).")
    unrebutted_hits_U: int = Field(..., description="Logical points made that opponent failed to address.")
    fallacies_F: int = Field(..., description="Count of formal/informal logical fallacies.")
    insinuations_I: int = Field(..., description="Count of bad-faith insinuations, loaded statements, or dog-whistles.")
    net_score: float = Field(..., description="Calculated via formula: (L * 3) + (U * 2) - (F * 2) - (I * 1.5)")
    integrity_ratio: float = Field(..., description="Calculated via formula: (L / (L + F + I)) * 100")


class SpeakerAnalysis(BaseModel):
    speaker_id: str = Field(..., description="Name or identifier of the speaker.")
    affiliation: str = Field(..., description="Stated or inferred debate stance (e.g., Left, Right, Affirmative).")
    talk_time_seconds: float = Field(..., description="Estimated total talk time in seconds.")
    talk_time_percentage: float = Field(..., description="Percentage of total debate talk time.")
    metrics: SpeakerMetrics


class TranscriptLedgerItem(BaseModel):
    timestamp: str = Field(..., description="Formatted timestamp (HH:MM:SS or MM:SS).")
    speaker: str = Field(..., description="Identifier of the speaker who made the statement.")
    category: str = Field(...,
                          description="One of: Logical Point (L), Unrebutted Hit (U), Fallacy (F), Insinuation (I)")
    quote: str = Field(..., description="Verbatim or close excerpt from transcript.")
    score_change: float = Field(..., description="Numerical score contribution (+3, +2, -2, or -1.5).")
    impact_explanation: str = Field(..., description="Brief, objective explanation of why this point was scored.")


class DebateAnalysisResponse(BaseModel):
    video_id: str
    total_duration_seconds: float
    speakers: List[SpeakerAnalysis]
    transcript_ledger: List[TranscriptLedgerItem]


# -------------------------------------------------------------------
# Utility Functions
# -------------------------------------------------------------------

def extract_video_id(url_or_id: str) -> str:
    """Extract 11-character YouTube video ID from various URL formats."""
    regex = r"(?:v=|\/|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url_or_id)
    if match:
        return match.group(1)
    if len(url_or_id) == 11:
        return url_or_id
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid YouTube URL or Video ID format."
    )


def fetch_and_format_transcript(video_id: str) -> tuple[str, float]:
    """
    Fetches transcript using YouTubeTranscriptApi and routes through Webshare proxies
    to bypass cloud host IP blocks.
    """
    try:
        # Check for multiple Webshare credentials in format: user1:pass1,user2:pass2
        credentials_env = os.getenv("WEBSHARE_CREDENTIALS")
        selected_user = None
        selected_pass = None

        if credentials_env:
            cred_pairs = [c.strip().split(":") for c in credentials_env.split(",") if ":" in c]
            if cred_pairs:
                selected_user, selected_pass = random.choice(cred_pairs)

        # Fallback to single username/password env vars
        if not selected_user or not selected_pass:
            selected_user = os.getenv("WEBSHARE_USERNAME")
            selected_pass = os.getenv("WEBSHARE_PASSWORD")

        # Initialize API with proxy configuration if credentials exist
        if selected_user and selected_pass:
            proxy_config = WebshareProxyConfig(
                proxy_username=selected_user,
                proxy_password=selected_pass
            )
            ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)
        else:
            ytt_api = YouTubeTranscriptApi()

        # Fetch raw transcript data list
        transcript_data = ytt_api.fetch(video_id, languages=['en', 'en-US'])

        # If fetch returns a FetchedTranscript object, convert to raw list
        if hasattr(transcript_data, "fetch"):
            raw_entries = transcript_data.fetch()
        else:
            raw_entries = transcript_data

        formatted_lines = []
        total_duration = 0.0

        for item in raw_entries:
            # Safely handle dictionary or object attributes
            start_sec = item['start'] if isinstance(item, dict) else item.start
            duration = item.get('duration', 0.0) if isinstance(item, dict) else getattr(item, 'duration', 0.0)
            text_val = item['text'] if isinstance(item, dict) else item.text

            total_duration = max(total_duration, start_sec + duration)

            start_int = int(start_sec)
            hours = start_int // 3600
            minutes = (start_int % 3600) // 60
            seconds = start_int % 60

            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"

            text_clean = text_val.replace('\n', ' ').strip()
            if text_clean:
                formatted_lines.append(f"[{time_str}] {text_clean}")

        if not formatted_lines:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript was empty for this video."
            )

        return "\n".join(formatted_lines), total_duration

    except (TranscriptsDisabled, NoTranscriptFound):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No English transcripts available for this video."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transcript: {str(e)}"
        )


# -------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------

@app.post(
    "/analyze-debate",
    response_model=DebateAnalysisResponse,
    summary="Analyze YouTube Debate Transcript",
    status_code=status.HTTP_200_OK
)
async def analyze_debate(request: DebateRequest):
    """
    Accepts a YouTube link, fetches timestamped captions, and evaluates debate participants
    quantitatively using strict mathematical metrics and Gemini structured output.
    """
    video_id = extract_video_id(request.youtube_url)

    # 1. Check if video has already been analyzed in the database
    with Session(engine) as session:
        statement = select(Debate).where(Debate.video_id == video_id)
        existing_debate = session.exec(statement).first()

        if existing_debate:
            # Return cached response instantly from SQLite
            return DebateAnalysisResponse(
                video_id=existing_debate.video_id,
                total_duration_seconds=existing_debate.total_duration_seconds,
                speakers=existing_debate.speakers_data,
                transcript_ledger=existing_debate.ledger_data
            )

    # 2. If not found in DB, fetch transcript using youtube-transcript-api
    transcript_text, total_duration = fetch_and_format_transcript(video_id)

    # Immutable evaluation rules fed directly to Gemini
    system_instruction = """
    You are an objective, impersonal, and analytical debate evaluator. Your task is to analyze transcript text,
    identify distinct speakers, quantify their talk times, and score them using the EXACT mathematical criteria below.

    EVALUATION CRITERIA & FORMULAS:
    - Logical Point (L): +3.0 pts | Valid argument with a Claim, Warrant, and Evidence.
    - Unrebutted Hit (U): +2.0 pts | A solid logical point left completely unaddressed by the opposing side.
    - Logical Fallacy (F): -2.0 pts | Structural logic errors (Strawman, Ad Hominem, False Dilemma, etc.).
    - Insinuation (I): -1.5 pts | Unsubstantiated claims, loaded questions, or bad-faith rhetoric.

    MATHEMATICAL SCORING FORMULAS:
    - Net Score = (L * 3) + (U * 2) - (F * 2) - (I * 1.5)
    - Integrity Ratio = (L / (L + F + I)) * 100

    INSTRUCTIONS:
    1. Parse speaker shifts from dialogue context and name mentions. Estimate total talk time per speaker.
    2. Maintain strict clinical neutrality. Do NOT judge political positions, only argument structure and logical validity.
    3. Output strictly according to the requested JSON Schema.
    """

    user_prompt = f"""
    Analyze the following transcript from YouTube Video ID: {video_id}. Total Duration: {total_duration} seconds.

    TRANSCRIPT:
    {transcript_text[:120000]}  # Trimmed to ensure fast processing context window
    """

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=DebateAnalysisResponse,
                temperature=0.1,  # Low temperature for analytical precision
            ),
        )

        # Parse structured response matching Pydantic model
        analysis_result = DebateAnalysisResponse.model_validate_json(response.text)
        analysis_result.video_id = video_id
        analysis_result.total_duration_seconds = total_duration

        # 3. Save the new analysis to SQLite
        with Session(engine) as session:
            db_record = Debate(
                video_id=video_id,
                youtube_url=request.youtube_url,
                total_duration_seconds=total_duration,
                speakers_data=[s.model_dump() for s in analysis_result.speakers],
                ledger_data=[l.model_dump() for l in analysis_result.transcript_ledger]
            )
            session.add(db_record)
            session.commit()

        return analysis_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gemini Evaluation Error: {str(e)}"
        )


@app.get("/debate/{video_id}", response_model=DebateAnalysisResponse)
def get_debate_by_id(video_id: str):
    """Retrieve a previously analyzed debate by its YouTube Video ID."""
    with Session(engine) as session:
        statement = select(Debate).where(Debate.video_id == video_id)
        debate = session.exec(statement).first()

        if not debate:
            raise HTTPException(
                status_code=404,
                detail="Debate not found in database. Analyze it first via POST /analyze-debate."
            )

        return DebateAnalysisResponse(
            video_id=debate.video_id,
            total_duration_seconds=debate.total_duration_seconds,
            speakers=debate.speakers_data,
            transcript_ledger=debate.ledger_data
        )


@app.get("/recent-debates")
def get_recent_debates():
    """Retrieve list of recently analyzed debates."""
    with Session(engine) as session:
        statement = select(Debate).order_by(Debate.created_at.desc()).limit(10)
        debates = session.exec(statement).all()
        return [
            {
                "video_id": d.video_id,
                "youtube_url": d.youtube_url,
                "created_at": d.created_at
            }
            for d in debates
        ]


@app.get("/")
def root():
    return {"message": "Debate Evaluation API is running. Navigate to /docs for OpenAPI documentation."}