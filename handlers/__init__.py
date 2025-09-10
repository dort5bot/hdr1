from .commands import router as commands_router
from .email_handlers import router as email_router

# Tüm handler'ları birleştirebilirsiniz
__all__ = ['commands_router', 'email_router']
