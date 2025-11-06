# Database package initialization
from .models import *

# Ensure all models are imported for Alembic auto-detection
__all__ = ["Chats"]