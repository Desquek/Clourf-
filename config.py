import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "clourf_secret")

    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

    UPLOAD_FOLDER = "static/uploads"

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
