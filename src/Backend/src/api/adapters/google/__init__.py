"""
Module of google adapters.
"""

from .bigquery import BigQuery
from .cloud_storage import CloudStorage
from .firebase import FirebaseAuth
from .looker import LookerDashboard
from .pubsub import MessagePublisher
from .secret_manager import SecretManager
from .speech_to_text import SpeechToText
from .speech_to_text_v2 import SpeechToTextV2, SpeechToTextV2Chirp

__all__ = (
    "BigQuery",
    "CloudStorage",
    "FirebaseAuth",
    "LookerDashboard",
    "MessagePublisher",
    "SecretManager",
    "SpeechToText",
    "SpeechToTextV2",
    "SpeechToTextV2Chirp",
)
