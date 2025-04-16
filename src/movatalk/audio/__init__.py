# movatalk/audio/__init__.py
"""
Moduł audio zawiera narzędzia do przetwarzania audio, rozpoznawania mowy (STT) i syntezy mowy (TTS).
"""

from movatalk.audio.processor import AudioProcessor
from movatalk.audio.stt import WhisperSTT
from movatalk.audio.tts import PiperTTS

__all__ = ['AudioProcessor', 'WhisperSTT', 'PiperTTS']