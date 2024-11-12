import os
import pyttsx3
from openai import OpenAI
import numpy as np
import logging
from dotenv import load_dotenv
from .text_to_speech import TextToSpeech

# Carrega as variáveis de ambiente
load_dotenv()

class SpeechHandler:
    def __init__(self, voice_speed_var=None):
        # Configura o logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Inicializa o cliente OpenAI com a chave de API explícita
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("Chave da API OpenAI não encontrada nas variáveis de ambiente")
            
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            self.logger.error(f"Erro ao inicializar o cliente OpenAI: {e}")
            self.client = None

        self.tts_engine = None
        self.stream = None
        self.please_interrupt = False
        self.text_to_speech = TextToSpeech(voice_speed_var=voice_speed_var)

    def init_tts_engine(self):
        """Inicializa o mecanismo TTS de voz do PC se ainda não estiver inicializado.""" 
        if not self.tts_engine:
            self.tts_engine = pyttsx3.init()
        return self.tts_engine

    def transcribe_audio(self, audio_file, use_local=False, use_spellcheck=False):
        """
        Transcreve áudio para texto usando Whisper local, API OpenAI ou com correção ortográfica.
        
        Args:
            audio_file: Objeto BytesIO contendo os dados de áudio
            use_local: Booleano indicando se deve usar o modelo Whisper local
            use_spellcheck: Booleano indicando se deve usar correção ortográfica
        """
        self.logger.info("Executando transcribe_audio")
        try:
            if use_spellcheck:
                selected_model = self.vars['chatgpt_model'].get()  # Obtém o modelo selecionado da UI
                return self.transcribe_with_spellcheck("Corrigir erros de ortografia", audio_file, selected_model)
            
            if use_local:
                import whisper
                local_model = whisper.load_model("base")
                audio_file.seek(0)
                audio_data = np.frombuffer(audio_file.read(), np.int16).astype(np.float32) / 32768.0
                result = local_model.transcribe(audio_data)
                return result.get("text", "")
            else:
                if not self.client:
                    raise ValueError("Cliente OpenAI não inicializado")
                
                audio_file.seek(0)
                
                # Registra informações detalhadas sobre a solicitação de transcrição
                self.logger.info(f"Detalhes da Solicitação de Transcrição:")
                self.logger.info(f"Modelo: whisper-1")
                self.logger.info(f"Tamanho do Arquivo: {len(audio_file.getvalue())} bytes")
                
                try:
                    audio_file.seek(0)  # Garante que o ponteiro do arquivo esteja no início
                    response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                    return response.text
                except Exception as api_error:
                    self.logger.error(f"Erro na Transcrição da API OpenAI: {api_error}")
                    return f"Erro na Transcrição: {api_error}"
        
        except Exception as e:
            self.logger.error(f"Erro na Transcrição: {e}")
            return f"Erro na Transcrição: {e}"

    def transcribe_with_spellcheck(self, system_message, audio_filepath, model):
        """
        Transcreve áudio e corrige erros de ortografia usando GPT-4.
        
        Args:
            system_message: Mensagem do sistema para guiar a correção
            audio_filepath: Caminho do arquivo de áudio a ser transcrito
            model: Modelo a ser usado para correção ortográfica
        """
        self.logger.info("Executando transcribe_with_spellcheck")
        completion = self.client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_message},
                {
                    "role": "user",
                    "content": self.transcribe_audio(audio_filepath),
                },
            ],
        )
        return completion.choices[0].message.content

    def get_available_voices(self, engine_type="tts-1"):
        """
        Obtém as vozes disponíveis para o mecanismo especificado.
        
        Args:
            engine_type: "tts-1" ou "Voz do PC"
        """
        if engine_type == "tts-1":
            return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        elif engine_type == "Voz do PC":
            engine = self.init_tts_engine()
            voices = engine.getProperty('voices')
            return [(voice.id, voice.name.split(' - ')[-1]) for voice in voices]
        return []

    def cleanup(self):
        """Limpa os recursos.""" 
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except Exception as e:
                self.logger.error(f"Erro durante a limpeza: {e}")
        
        if self.text_to_speech:
            try:
                self.text_to_speech.cleanup()
            except Exception as e:
                self.logger.error(f"Erro durante a limpeza do TextToSpeech: {e}")
