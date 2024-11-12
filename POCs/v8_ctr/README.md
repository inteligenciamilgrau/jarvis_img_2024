# Junin v8

Uma aplicação de chatbot moderna com tema escuro, capacidades avançadas de interação por voz e automação de computador.

## Novos Recursos

### Seleção de Dispositivo de Áudio
- Menus suspensos para selecionar dispositivos de áudio de entrada e saída
- Retorno automático aos dispositivos padrão do sistema
- Suporta múltiplos dispositivos de entrada/saída de áudio
- Configuração flexível de dispositivos sem reiniciar a aplicação

### Automação de Computador
- Integração com Anthropic para controle do computador
- Captura de tela e análise de imagem
- Controle de mouse e teclado
- Execução de tarefas automatizadas

### Sistema de Tarefas Dinâmico
- Carregamento dinâmico de tarefas
- Sistema de plugins extensível
- Gerenciamento flexível de comandos

## Melhorias em relação à v7

1. **Interface Moderna com Tema Escuro**
   - Design moderno e elegante com tema escuro
   - Hierarquia visual e legibilidade aprimoradas
   - Componentes de UI modernos com estilo personalizado

2. **Arquitetura Modular Aprimorada**
   - Organização clara de componentes e responsabilidades
   - Sistema de plugins para tarefas
   - Gerenciamento de estado e configurações melhorado
   - Melhor manutenção e extensibilidade do código

3. **Manuseio de Áudio Aprimorado**
   - Seleção avançada de dispositivos
   - Gerenciamento robusto de dispositivos de entrada/saída
   - Detecção de atividade de voz (VAD) aprimorada

## Estrutura do Projeto

```
junin_v8/
├── config/
│   └── theme.py           # Configuração de tema e áudio
├── modules/
│   ├── audio_handler.py   # Gravação de áudio e gerenciamento de dispositivos
│   ├── chat_handler.py    # Interações de chat e API
│   ├── speech_handler.py  # Texto para fala e fala para texto
│   ├── computer_control.py # Controle do computador via Anthropic
│   ├── text_to_speech.py  # Sistema TTS independente
│   └── task_manager.py    # Gerenciamento de tarefas dinâmicas
├── ui/
│   ├── components.py      # Componentes modernos de UI
│   ├── app_layout.py      # Layout da aplicação
│   ├── settings_manager.py # Gerenciamento de configurações
│   └── event_handlers.py  # Manipuladores de eventos
├── tasks_folder/          # Tarefas dinâmicas carregáveis
│   ├── handle_normal.py   # Tarefa padrão
│   ├── handle_click.py    # Tarefa de clique
│   └── handle_image.py    # Tarefa de imagem
├── app.py                # Aplicação principal
└── requirements.txt      # Dependências do projeto
```

## Recursos

- Interface moderna com tema escuro
- Interação por voz com suporte a VAD
- Múltiplos motores TTS (OpenAI e local)
- Múltiplos backends de chat (OpenAI e Ollama)
- Seleção de dispositivo de áudio
- Automação de computador via Anthropic
- Sistema de tarefas dinâmico
- Configurações personalizáveis
- Preferências de usuário persistentes
- Suporte a teclas de atalho globais
- Transcrição em tempo real

## Requisitos

- Python 3.8+
- Chave da API OpenAI
- Chave da API Anthropic (para automação de computador)
- Bibliotecas de áudio em nível de sistema
- Dependências listadas em requirements.txt

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Instale as dependências de áudio em nível de sistema:
   - Windows: Instale o Microsoft Visual C++ Build Tools
   - Linux: `sudo apt-get install python3-pyaudio`
   - macOS: `brew install portaudio`

4. Instale as dependências do Python:
   ```bash
   pip install -r requirements.txt
   ```

5. Crie um arquivo .env com suas chaves de API:
   ```
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   ```

## Uso

1. Execute a aplicação:
   ```bash
   python app.py
   ```

2. Recursos:
   - Selecione dispositivos de áudio de entrada e saída
   - Digite mensagens na área de entrada
   - Clique no botão de gravação ou use Ctrl+Alt para gravar voz
   - Ative o VAD para detecção automática de voz
   - Escolha entre diferentes vozes TTS
   - Selecione o idioma preferido
   - Ative/desative a fala de resposta
   - Alternar janela sempre no topo
   - Use comandos para automação do computador
   - Adicione novas tarefas na pasta tasks_folder

## Atalhos de Teclado

- `Ctrl+Alt`: Alternar gravação de voz
- `Enter`: Enviar mensagem
- `Shift+Enter`: Nova linha na entrada

## Desenvolvimento de Tarefas

Para criar uma nova tarefa:

1. Crie um arquivo .py na pasta tasks_folder
2. Defina as variáveis:
   - description: Descrição da tarefa
   - trigger: Palavras-chave que ativam a tarefa
   - example: Exemplo de uso
3. Implemente a função execute(content)

Exemplo:
```python
description = "Executa uma ação específica"
trigger = "palavras-chave que ativam esta tarefa"
example = "Exemplo de como usar esta tarefa"

def execute(content):
    # Implementação da tarefa
    return resultado
```

## Contribuindo

Sinta-se à vontade para enviar problemas e solicitações de melhorias!

## Licença

Licença MIT
