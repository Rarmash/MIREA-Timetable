import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mirea:mirea@localhost:5432/mirea",
)
SCHEDULE_API_URL = os.getenv("SCHEDULE_API_URL", "http://localhost:8000").rstrip("/")
SCHEDULE_API_TIMEOUT = float(os.getenv("SCHEDULE_API_TIMEOUT", "3.0"))
