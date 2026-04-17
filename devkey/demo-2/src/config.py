"""Shared configuration for the multi-agent demo.

Explicit is better than implicit.
Simple is better than complex.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# GCP Configuration
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
BUCKET_URI = os.environ.get("BUCKET_URI")


def validate_config():
    """Validate required configuration is set."""
    required = {
        "GOOGLE_CLOUD_PROJECT": GOOGLE_CLOUD_PROJECT,
        "BUCKET_URI": BUCKET_URI,
    }

    missing = [k for k, v in required.items() if not v]

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Check your .env file."
        )

    return True


def get_api_endpoint():
    """Get the Vertex AI API endpoint for the configured location."""
    return f"https://{GOOGLE_CLOUD_LOCATION}-aiplatform.googleapis.com"
