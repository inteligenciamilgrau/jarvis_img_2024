import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from modules.open_ai.tts.tts import OpenAITTS
from modules.open_ai.tts.pc_voice import PCVoiceTTS
from modules.open_ai.stt.stt import SpeechToText

# Carrega as variáveis de ambiente
load_dotenv()

# Configuração do logger
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

class SpeechHandler:
    def __init__(self, task_manager, voice_speed_var=None, accent_var=None, emotion_var=None, intonation_var=None, vars=None):
        # Inicializa o cliente OpenAI com a chave de API explícita
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("Chave da API OpenAI não encontrada nas variáveis de ambiente")
            
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            log.error("Erro ao inicializar o cliente OpenAI: %s", e)
            self.client = None

        # Armazena o TaskManager
        self.task_manager = task_manager

        # Inicializa os engines TTS
        self.openai_tts = OpenAITTS(
            voice_speed_var=voice_speed_var,
            accent_var=accent_var,
            emotion_var=emotion_var,
            intonation_var=intonation_var
        )
        self.pc_tts = PCVoiceTTS(voice_speed_var=voice_speed_var)
        self.current_engine = vars['voice_engine'].get() if vars else "tts-1"
        self.vars = vars

        # Se o engine inicial for tts-gpt4, configura skip_transcription como True
        if self.current_engine == "tts-gpt4":
            self.openai_tts.skip_transcription = True
            log.info("Inicializado com TTS-GPT4, skip_transcription definido como True")

    def set_input_audio(self, audio_base64, skip_transcription=False):
        """
        Define o áudio de entrada para o TTS-GPT4.
        
        Args:
            audio_base64: Áudio em formato base64
            skip_transcription: Se True, pula a etapa de transcrição
        """
        if self.current_engine == "tts-gpt4":
            self.openai_tts.set_input_audio(audio_base64, skip_transcription)

    def set_transcript_callback(self, callback):
        """
        Define o callback para atualizar o texto do chat com a transcrição.
        
        Args:
            callback: Função a ser chamada quando houver uma nova transcrição
        """
        if self.current_engine == "tts-gpt4":
            self.openai_tts.set_transcript_callback(callback)

    def get_available_voices(self, engine_type="tts-1"):
        """
        Obtém as vozes disponíveis para o mecanismo especificado.
        
        Args:
            engine_type: "tts-1", "tts-1-hd", "tts-gpt4" ou "Voz do PC"
            
        Returns:
            Lista de vozes disponíveis
        """
        if engine_type in ["tts-1", "tts-1-hd", "tts-gpt4"]:
            # Todos os engines OpenAI compartilham as mesmas vozes
            return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        elif engine_type == "Voz do PC":
            engine = self.pc_tts._ensure_pc_engine()
            voices = engine.getProperty('voices')
            # Extrai apenas o último nome da voz do caminho completo
            return [voice.id.split('\\')[-1] for voice in voices]
        return []

    def set_voice(self, voice, engine_type="tts-1"):
        """
        Define a voz a ser usada.
        
        Args:
            voice: ID da voz a ser usada
            engine_type: "tts-1", "tts-1-hd", "tts-gpt4" ou "Voz do PC"
        """
        self.current_engine = engine_type
        if engine_type in ["tts-1", "tts-1-hd", "tts-gpt4"]:
            self.openai_tts.set_voice(voice)
            self.openai_tts.set_model(engine_type)  # Define o modelo específico
            # Define skip_transcription como True se for tts-gpt4
            self.openai_tts.skip_transcription = (engine_type == "tts-gpt4")
            log.info("Engine alterado para %s, skip_transcription: %s", engine_type, self.openai_tts.skip_transcription)
        else:
            # Para vozes do PC, precisamos reconstruir o caminho completo
            engine = self.pc_tts._ensure_pc_engine()
            voices = engine.getProperty('voices')
            full_voice_id = next((v.id for v in voices if v.id.split('\\')[-1] == voice), None)
            if full_voice_id:
                self.pc_tts.set_voice(full_voice_id)
            else:
                log.error("Voz não encontrada: %s", voice)

    def speak_response(self, text, on_speech_start=None):
        """
        Reproduz o texto usando o engine atual.
        
        Args:
            text: Texto a ser reproduzido
            on_speech_start: Callback para quando a fala começar
        """
        if self.current_engine in ["tts-1", "tts-1-hd", "tts-gpt4"]:
            self.openai_tts.speak_response(text, on_speech_start)
        else:
            self.pc_tts.speak_response(text, on_speech_start)

    def stop_speaking(self):
        """Para a reprodução atual."""
        if self.current_engine in ["tts-1", "tts-1-hd", "tts-gpt4"]:
            self.openai_tts.stop_speaking()
        else:
            self.pc_tts.stop_speaking()

    def enqueue_speak(self, text, on_speech_start=None):
        """Adiciona texto à fila de fala."""
        if self.current_engine in ["tts-1", "tts-1-hd", "tts-gpt4"]:
            self.openai_tts.enqueue_speak(text, on_speech_start)
        else:
            self.pc_tts.enqueue_speak(text, on_speech_start)

    def cleanup(self):
        """Limpa os recursos."""
        try:
            self.openai_tts.cleanup()
            self.pc_tts.cleanup()
        except Exception as e:
            log.error("Erro durante a limpeza: %s", e)

    def handle_recording_complete(self, audio_file):
        """Manipula a conclusão da gravação e transcreve o áudio."""
        stt = SpeechToText(self.client, log, self.task_manager, self.vars)
        
        # Verifica o modo de transcrição selecionado na UI
        whisper_mode = self.vars['whisper'].get() if self.vars else "Online"
        log.info("Modo de transcrição selecionado: %s", whisper_mode)
        
        use_local = whisper_mode == "Local"
        use_spellcheck = whisper_mode == "Com Correção Ortográfica"
        
        log.info("Usando modo de transcrição: %s", 'com correção ortográfica' if use_spellcheck else 'local' if use_local else 'normal')
        log.info("Parâmetros de transcrição: use_local=%s, use_spellcheck=%s", use_local, use_spellcheck)
        
        # Retorna o texto transcrito e indica se foi corrigido
        return stt.transcribe_audio(audio_file, use_local=use_local, use_spellcheck=use_spellcheck), use_spellcheck
