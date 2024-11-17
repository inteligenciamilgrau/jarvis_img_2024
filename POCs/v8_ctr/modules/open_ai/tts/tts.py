from .tts_standard import StandardTTS
from .tts_chat_completions import ChatCompletionsTTS

class OpenAITTS:
    """
    Classe principal que gerencia diferentes implementações TTS.
    Atua como uma fábrica para criar a implementação apropriada com base no modelo.
    """
    def __init__(self, voice_speed_var=None, accent_var=None, emotion_var=None, intonation_var=None):
        self._tts_instance = None
        self._current_model = None
        self.voice_speed_var = voice_speed_var
        self.accent_var = accent_var
        self.emotion_var = emotion_var
        self.intonation_var = intonation_var

    def _ensure_correct_instance(self, model):
        """
        Garante que a instância correta do TTS está sendo usada com base no modelo.
        Cria uma nova instância se necessário.
        """
        if model != self._current_model:
            # Limpa a instância anterior se existir
            if self._tts_instance:
                self._tts_instance.cleanup()

            # Cria a nova instância apropriada
            if model == "tts-gpt4":
                self._tts_instance = ChatCompletionsTTS(
                    voice_speed_var=self.voice_speed_var,
                    accent_var=self.accent_var,
                    emotion_var=self.emotion_var,
                    intonation_var=self.intonation_var
                )
            else:
                self._tts_instance = StandardTTS(self.voice_speed_var)
            
            self._current_model = model

    def set_input_audio(self, audio_data_base64, skip_transcription=False):
        """Define o áudio de entrada para o TTS-GPT4."""
        if isinstance(self._tts_instance, ChatCompletionsTTS):
            self._tts_instance.set_input_audio(audio_data_base64, skip_transcription)

    def set_transcript_callback(self, callback):
        """Define o callback para atualizar o texto do chat com a transcrição."""
        if isinstance(self._tts_instance, ChatCompletionsTTS):
            self._tts_instance.set_transcript_callback(callback)

    def set_voice(self, voice):
        """Define a voz a ser usada."""
        if self._tts_instance:
            self._tts_instance.set_voice(voice)

    def set_model(self, model):
        """Define o modelo a ser usado."""
        self._ensure_correct_instance(model)
        if self._tts_instance:
            self._tts_instance.set_model(model)

    def speak_response(self, response_text, on_speech_start=None):
        """Processa e reproduz o texto como áudio."""
        if self._tts_instance:
            self._tts_instance.speak_response(response_text, on_speech_start)

    def stop_speaking(self):
        """Para a reprodução atual."""
        if self._tts_instance:
            self._tts_instance.stop_speaking()

    def enqueue_speak(self, response_text, on_speech_start=None):
        """Adiciona texto à fila de fala."""
        if self._tts_instance:
            self._tts_instance.enqueue_speak(response_text, on_speech_start)

    def cleanup(self):
        """Limpa os recursos do TTS."""
        if self._tts_instance:
            self._tts_instance.cleanup()
            self._tts_instance = None
