from io import BytesIO
import base64
from openai import OpenAI
from PIL import Image
import mss
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Metadados para esta tarefa
description = "Lida com uma solicitação sobre uma imagem."
trigger = "Se o usuário perguntar sobre a tela ou imagem, o tipo é 'image' e passe a pergunta como conteúdo."
example = "{'type': 'handle_image', 'content': 'Pergunta sobre a imagem'}"

def capture_and_show_image_from_second_monitor(width=400, height=400):
    # Inicializa mss para captura de tela
    with mss.mss() as sct:
        # Obtém as informações do monitor
        monitors = sct.monitors
        
        # Verifica se há um segundo monitor disponível
        if len(monitors) < 2:
            raise ValueError("Nenhum segundo monitor detectado.")
        
        # O monitor 2 está no índice 2 (o índice 1 é o monitor principal)
        second_monitor = monitors[2]
        
        # Define a região para capturar: 400x400 a partir do canto superior esquerdo do segundo monitor
        capture_region = {
            "top": second_monitor["top"],
            "left": second_monitor["left"],
            "width": width,
            "height": height
        }
        
        # Captura a tela na região definida
        screenshot = sct.grab(capture_region)
        
        # Converte para uma imagem PIL
        return Image.frombytes("RGB", screenshot.size, screenshot.rgb)

def ler_tela(message, model="gpt-4o-mini"):
    client = OpenAI()

    image = capture_and_show_image_from_second_monitor(1920, 1080)
    buffered = BytesIO()
    image.save(buffered, format="PNG")  # Salva a imagem no buffer como formato PNG
    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64," + base64_image,
                        }
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    log.info("Resposta: %s", response.choices[0].message.content)
    return response.choices[0].message.content

# Função que lida com a tarefa
def execute(content, model="gpt-4o-mini"):
    resposta = ler_tela(content, model)
    return resposta
