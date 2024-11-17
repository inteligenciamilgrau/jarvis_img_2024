import asyncio
import time
import numpy as np
from .tts_base import BaseTTS
from .audio_processor import AudioChunkProcessor
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class ChatCompletionsTTS(BaseTTS):
    """Implementação TTS usando Chat Completions com suporte a áudio"""
    def __init__(self, voice_speed_var=None, accent_var=None, emotion_var=None, intonation_var=None):
        super().__init__(voice_speed_var)
        self.last_transcript = None
        self.input_audio_data = None
        self.skip_transcription = False
        self.transcript_callback = None
        self.chunk_processor = AudioChunkProcessor()
        self.accent_var = accent_var
        self.emotion_var = emotion_var
        self.intonation_var = intonation_var
        self.current_audio_data = None

    def set_input_audio(self, audio_data_base64, skip_transcription=False):
        """Define o áudio de entrada em base64 para uso com TTS-GPT4."""
        log.info("=== Debug: set_input_audio ===")
        log.info("Definindo input_audio_data. Tamanho do áudio: %d", len(audio_data_base64) if audio_data_base64 else 0)
        log.info("Skip transcription: %s", skip_transcription)
        
        self.input_audio_data = audio_data_base64
        self.skip_transcription = skip_transcription
        log.info("Áudio de entrada definido com sucesso")

    def set_transcript_callback(self, callback):
        """Define o callback para atualizar o texto do chat com a transcrição."""
        self.transcript_callback = callback
        log.info("Callback de transcrição definido")

    def speak_response(self, response_text, on_speech_start=None):
        """Processa e reproduz o texto como áudio usando Chat Completions."""
        if self._shutdown or not response_text.strip():
            return
            
        try:
            log.info("=== Iniciando speak_response (TTS-GPT4) ===")
            log.info("Texto recebido: %s", response_text)
            
            # Para qualquer reprodução em andamento
            self.stop_speaking()
            
            self.is_speaking = True
            self.stop_current = False
            self.first_chunk_played = False
            self.speech_started_callback = on_speech_start

            if not self.audio_stream.ensure_stream():
                return

            log.info("=== Processando com TTS-GPT4 ===")
            self._generate_and_play_audio(response_text.strip())
                
            log.info("=== Finalizando speak_response ===")

        except Exception as e:
            log.error("Erro durante a conversão de texto em fala: %s", e)
            import traceback
            traceback.print_exc()
        finally:
            self.is_speaking = False
            self.stop_current = False
            self.first_chunk_played = False
            self.speech_started_callback = None

    def _generate_and_play_audio(self, text):
        """Gera e reproduz áudio usando Chat Completions."""
        try:
            log.info("=== Iniciando nova geração de áudio (TTS-GPT4) ===")
            log.info("Texto de entrada: %s", text)
            log.info("Voz atual: %s", self.voice)
            
            self.api_start_time = time.time()
            
            messages = self._prepare_messages(text)
            completion = self._make_api_call(messages)
            api_response_time = time.time() - self.api_start_time

            audio_data = completion.choices[0].message.audio.data
            transcript = completion.choices[0].message.audio.transcript
            
            self._handle_transcript(transcript)
            
            # Processa todo o áudio antes de começar a reprodução
            all_samples = []
            for chunk in self.chunk_processor.process_base64_chunks(audio_data):
                if self.stop_current or self._shutdown:
                    break
                    
                if len(chunk) > 0:
                    all_samples.append(chunk)

            if all_samples and not self.stop_current and not self._shutdown:
                # Concatena todos os chunks em um único array
                final_samples = np.concatenate(all_samples)
                
                # Aplica fade in/out para suavizar o áudio
                fade_length = min(len(final_samples), 1024)
                fade_in = np.linspace(0.0, 1.0, fade_length)
                fade_out = np.linspace(1.0, 0.0, fade_length)
                
                final_samples[:fade_length] *= fade_in
                final_samples[-fade_length:] *= fade_out
                
                # Reproduz o áudio processado
                if self.speech_started_callback:
                    self.speech_started_callback()
                self.audio_stream.play_audio_chunks(final_samples)
            
            if self.skip_transcription:
                self.input_audio_data = None
                self.skip_transcription = False
            
        except Exception as e:
            log.error("Erro ao gerar áudio com Chat Completions TTS: %s", e)

    def _prepare_messages(self, text):
        """Prepara as mensagens para a API incluindo system prompt e user message."""
        log.info("=== Debug: _prepare_messages ===")
        log.info("Texto recebido: %s", text)
        log.info("Skip transcription: %s", self.skip_transcription)
        log.info("Input audio data presente: %s", self.input_audio_data is not None)

        # Constrói a instrução de voz baseada nas configurações
        voice_instruction = "Por favor, escute o áudio e forneça uma resposta apropriada e natural"
        
        # Adiciona sotaque se não for default
        if self.accent_var and self.accent_var.get() != "Default (Sem sotaque)":
            voice_instruction += f", falando com sotaque {self.accent_var.get().lower()}"
        
        # Adiciona velocidade
        if self.voice_speed_var:
            voice_instruction += f", e falando bem devagar como {self.voice_speed_var.get()} de velocidade"

        # Adiciona entonação se não for default
        if self.intonation_var and self.intonation_var.get() != "Default (Sem entonação)":
            voice_instruction += f", com a entonação {self.intonation_var.get().lower()}"
        
        # Adiciona emoção se não for default
        if self.emotion_var and self.emotion_var.get() != "Default (Sem emoção)":
            voice_instruction += f", {self.emotion_var.get().lower()}"

        # Log da instrução de voz completa
        log.info("=== Instrução de Voz Completa ===")
        log.info("Instrução: %s", voice_instruction)
        log.info("Velocidade atual: %s", self.voice_speed_var.get() if self.voice_speed_var else "1.5")
        log.info("Sotaque atual: %s", self.accent_var.get() if self.accent_var else "Default (Sem sotaque)")
        log.info("Entonação atual: %s", self.intonation_var.get() if self.intonation_var else "Default (Sem entonação)")
        log.info("Emoção atual: %s", self.emotion_var.get() if self.emotion_var else "Default (Sem emoção)")

        # Se temos áudio e skip_transcription, enviamos apenas a mensagem com o áudio
        if self.input_audio_data and self.skip_transcription:
            log.info("Usando modo de áudio direto (sem transcrição)")
            return [{
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": voice_instruction
                    },
                    {
                        "type": "input_audio", 
                        "input_audio": {
                            "data": self.input_audio_data, 
                            "format": "wav"
                        }
                    }
                ]
            }]
        
        # Se estamos processando áudio mas ainda não o recebemos, aguardamos
        if text == "Processando áudio...":
            log.info("Aguardando áudio...")
            return [{
                "role": "user",
                "content": "Aguardando áudio..."
            }]
        
        # Para modo de texto normal, incluímos o system prompt
        log.info("Usando modo de texto normal")
        return [
            {
                "role": "system",
                "content": "Você é um assistente virtual inteligente e prestativo. Seu objetivo é entender e responder às perguntas e comandos do usuário de forma natural e eficiente. Mantenha suas respostas diretas e relevantes."
            },
            {
                "role": "user",
                "content": text
            }
        ]

    def _make_api_call(self, messages):
        """Faz a chamada à API do Chat Completions."""
        return self.client_openai.chat.completions.create(
            model="gpt-4o-audio-preview",
            modalities=["text", "audio"],
            audio={"voice": self.voice, "format": "mp3"},
            messages=messages
        )

    def _handle_transcript(self, transcript):
        """Processa a transcrição recebida."""
        log.info("=== Dados da resposta ===")
        log.info("Transcrição recebida: %s", transcript)
        
        if self.skip_transcription and self.transcript_callback:
            self.transcript_callback(transcript)
        
        self.last_transcript = transcript

    def stop_speaking(self):
        """Para a reprodução atual e limpa os recursos."""
        self.stop_current = True
        if self.audio_stream and self.audio_stream.stream:
            self.audio_stream.cleanup()
            self.audio_stream.ensure_stream()  # Reinicializa o stream
        self.is_speaking = False
