from io import BytesIO
import base64
import threading
import replicate
import re
import pyautogui
import matplotlib.pyplot as plt
import mss
from PIL import Image
from modules.computer_use_handler import AnthropicToolHandler

setar_molmo = False

if setar_molmo:
    # Metadados para esta tarefa
    description = "Lida com o clique em uma parte da tela."
    trigger = """Se o usuário pedir para clicar ou apontar para algo, o tipo é 'click'.
    O conteúdo do clique deve estar sempre em inglês começando com 'point to the...'"""
    example = "{'type': 'handle_click', 'content': 'point to the ...'}"
else:
    description = """Usa o computador para buscar na internet, e clicar em sites, botões ou notícias.
    Informe onde deseja clicar, ou o site que quer acessar, ou a busca que gostaria de fazer.
    Explique na forma de texto como no exemplo:
        'Clique no instagram'
        'Busque no google um site de viagens'
    """
    trigger = """Se o usuário pedir para clicar, fazer uma busca ou quiser ver algo na tela, rode isto'"""
    example = "{'type': 'handle_click', 'content': 'Clique no ...'}"

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

def click_on(click_this):
    segundo_monitor_pixels = 1920
    image = capture_and_show_image_from_second_monitor(1920, 1080)
    buffered = BytesIO()
    image.save(buffered, format="PNG")  # Salva a imagem no buffer como formato PNG
    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

    print("Chamando replicate")
    # Executa o modelo e obtém a saída
    output = replicate.run(
        "zsxkib/molmo-7b:76ebd700864218a4ca97ac1ccff068be7222272859f9ea2ae1dd4ac073fa8de8",
        input={
            "text": click_this,
            "image": "data:image/png;base64," + base64_image,
            "top_k": 100,
            "top_p": 1,
            "temperature": 1,
            "length_penalty": 1,
            "max_new_tokens": 1000
        }
    )

    # Imprime a saída para verificar sua estrutura
    print("Output:", output)

    # Padrão para extrair coordenadas x e y da saída, seja no formato <point> ou <points>
    pattern = r'x\d*="([\d.]+)" y\d*="([\d.]+)"'
    matches = re.findall(pattern, output)

    # Converte as strings extraídas em valores float e armazena como uma lista de tuplas
    coordinates = [(float(x), float(y)) for x, y in matches]

    # Imprime as coordenadas
    print("Coordenadas dos pontos:")
    for i, (x, y) in enumerate(coordinates):
        print(f"Ponto {i + 1}: ({x + segundo_monitor_pixels}, {y})")

    # Converte coordenadas de relativas para posições de pixel
    width, height = image.size
    x_coords = [x / 100 * width for x, y in coordinates]
    y_coords = [y / 100 * height for x, y in coordinates]

    # Após extrair as coordenadas
    for x, y in zip(x_coords, y_coords):
        pyautogui.moveTo(x + segundo_monitor_pixels, y, duration=0.5)  # Move o cursor do mouse para as coordenadas
        pyautogui.click()  # Clica com o mouse nas coordenadas

    # Plota pontos na imagem
    plotar = False
    if plotar:
        # Exibe a imagem e os pontos
        fig, ax = plt.subplots()
        ax.imshow(image)

        ax.scatter(x_coords, y_coords, color='black', s=400, marker='o')

        print("coords", x_coords, y_coords, image.size)

        with mss.mss() as sct:
            # Obtém a posição do segundo monitor
            second_monitor = sct.monitors[2]
            x_pos, y_pos = second_monitor["left"], second_monitor["top"]

            # Define a posição da figura no segundo monitor
            fig.canvas.manager.window.wm_geometry(f"+{x_pos}+{y_pos + 600}")

            # Mostra o gráfico com os pontos
            plt.title("Coordenadas na Imagem")
            plt.show()
    return output

def chat_handler_thread(message):
    print("Usando PC!", message)
    handler = AnthropicToolHandler(monitor_index=2, monitor_offset=[1920, 0], falar=False)
    print("Iniciando ferramenta")
    result = handler.handle_chat(message)
    # Faça algo com o resultado se necessário
    print(result)

# Função que lida com a tarefa
def execute(content):
    print("Clique:", content)

    if setar_molmo:
        click_on(content)
        return content
    else:
        message_thread = threading.Thread(target=chat_handler_thread, args=(content,))
        # Inicia a thread
        message_thread.start()

        #return str(result)
        return "Deu certo?"
