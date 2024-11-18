"""
Módulo TTS (Text-to-Speech) que fornece diferentes implementações de síntese de voz.

Classes principais:
- OpenAITTS: Classe principal que gerencia diferentes implementações TTS
- StandardTTS: Implementação do TTS padrão usando o modelo tts-1
- ChatCompletionsTTS: Implementação TTS usando Chat Completions com suporte a áudio
"""

from .tts import OpenAITTS
from .tts_standard import StandardTTS
from .tts_chat_completions import ChatCompletionsTTS
from .tts_base import BaseTTS
from .audio_processor import AudioChunkProcessor, AudioStreamManager

__all__ = [
    'OpenAITTS',
    'StandardTTS',
    'ChatCompletionsTTS',
    'BaseTTS',
    'AudioChunkProcessor',
    'AudioStreamManager'
]
