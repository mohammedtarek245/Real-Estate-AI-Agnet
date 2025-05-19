"""
Configuration file for the Arabic Real Estate AI Agent.
Contains all configuration parameters and constants.
"""

import os
from enum import Enum
from pathlib import Path

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "knowledge" / "data"
PHASE_KNOWLEDGE_DIR = DATA_DIR / "phase_knowledge"
PROPERTIES_PATH = DATA_DIR / "properties.csv"
AREA_INSIGHTS_PATH = DATA_DIR / "area_insights.csv"
MARKET_TRENDS_PATH = DATA_DIR / "market_trends.csv"
INVESTMENT_TIPS_PATH = DATA_DIR / "investment_tips.csv"
MORTGAGE_INFO_PATH = DATA_DIR / "mortgage_info.csv"
FURNISHING_GUIDE_PATH = DATA_DIR / "furnishing_guide.csv"
LEGAL_GUIDE_PATH = DATA_DIR / "legal_guide.csv"
VISIT_TIPS_PATH = DATA_DIR / "visit_tips.csv"

VECTOR_DB_PATH = BASE_DIR / "vector_db"

# === Agent behavior ===
DEFAULT_LANGUAGE = "ar"
DEFAULT_DIALECT = "Egyptian"
MAX_HISTORY_LENGTH = 10
TEMPERATURE = 0.7
TOP_P = 0.9

# === RAG configurations ===
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 128
TOP_K_RETRIEVAL = 3

# === UI configurations ===
GRADIO_THEME = "dark"
UI_TITLE = "وكيل العقارات الذكي"
UI_DESCRIPTION = "مرحبًا بك في وكيل العقارات الذكي. يمكنني مساعدتك في العثور على العقار المناسب لاحتياجاتك."
UI_WELCOME_MESSAGE = "اهلا بيك انا مساعدك العقاري. تحب اساعدك ازاي؟"

# === Debugging ===
DEBUG = os.getenv("DEBUG", "False").lower() in ["1", "true", "yes"]

# === Conversation Phase Enumeration ===
class ConversationPhase(Enum):
    DISCOVERY = 1       # Initial client qualification
    SUMMARY = 2         # Summary confirmation
    SUGGESTION = 3      # Property suggestion
    PERSUASION = 4      # Build value for selected property
    ALTERNATIVE = 5     # Address concerns with alternatives
    URGENCY = 6         # Create urgency
    CLOSING = 7         # Facilitate next steps
