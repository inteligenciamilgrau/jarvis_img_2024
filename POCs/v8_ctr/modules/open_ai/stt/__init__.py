"""
Módulo STT (Speech-to-Text) que fornece diferentes implementações de transcrição de fala.

Classes principais:
- SpeechToText: Classe principal que gerencia diferentes implementações de transcrição
- OpenAITranscriber: Implementação usando a API OpenAI
- LocalTranscriber: Implementação usando Whisper localmente
- SpellcheckTranscriber: Implementação com correção ortográfica usando GPT
"""

from .stt import SpeechToText
from .openai_transcriber import OpenAITranscriber
from .local_transcriber import LocalTranscriber
from .spellcheck_transcriber import SpellcheckTranscriber
from .base_transcriber import BaseTranscriber

__all__ = [
    'SpeechToText',
    'OpenAITranscriber',
    'LocalTranscriber',
    'SpellcheckTranscriber',
    'BaseTranscriber'
]
