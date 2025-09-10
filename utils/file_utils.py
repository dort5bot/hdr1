import os
import logging
from config import TEMP_DIR, processed_mail_ids

logger = logging.getLogger(__name__)

async def cleanup_temp():
    """Clean up temp directory"""
    for filename in os.listdir(TEMP_DIR):
        filepath = os.path.join(TEMP_DIR, filename)
        try:
            if os.path.isfile(filepath):
                os.unlink(filepath)
        except Exception as e:
            logger.error(f"Error deleting {filepath}: {e}")
    
    processed_mail_ids.clear()
    logger.info("Temp directory cleaned up")