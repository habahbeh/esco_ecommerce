# products/rag/logger.py
import logging
from datetime import datetime

# إعداد نظام التتبع
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('RAG_System')

def log_step(step_name, data=None):
    """سجل كل خطوة للتتبع"""
    logger.info(f"📍 {step_name}")
    if data:
        logger.debug(f"   البيانات: {data}")