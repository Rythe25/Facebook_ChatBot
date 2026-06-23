"""
app/config.py
Central configuration for the whole bot. Every setting comes from the `.env`
file via pydantic-settings, so there are NO hardcoded secrets in the code.
Anywhere you need an API key or option, do: `from app.config import settings`.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- LLM provider ---
    # "gemini" (default — no international Visa card needed) or "openai".
    llm_provider: str = "gemini"
    openai_api_key: str = ""
    google_api_key: str = ""          # used by Gemini

    # --- Vector DB (Pinecone) ---
    pinecone_api_key: str = ""
    pinecone_index_name: str = "fanpage-faqs"

    # --- Facebook ---
    fb_verify_token: str = ""         # any random string; must match Meta webhook config
    fb_page_access_token: str = ""    # long-lived token, expires every 60 days

    # --- Google Sheets ---
    google_sheets_credentials_path: str = "./credentials/service-account.json"
    google_sheets_id: str = ""

    # --- Misc ---
    log_level: str = "INFO"

    # Read variables from a .env file in the project root.
    # Field names are matched to env vars case-insensitively (e.g. FB_VERIFY_TOKEN).
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# One shared settings instance, imported across the app.
settings = Settings()
