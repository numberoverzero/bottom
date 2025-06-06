"""asyncio-based rfc2812-compliant IRC Client"""
from .client import Client, rfc2812_handler
from .protocol import Protocol


__all__ = ["Client", "Protocol", "rfc2812_handler"]
__version__ = "3.0.0"
