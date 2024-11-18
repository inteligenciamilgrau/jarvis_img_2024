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
- Configuração de monitor e offset personalizado

### Sistema de Tarefas Dinâmico
- Carregamento dinâmico de tarefas
- Sistema de plugins extensível
- Gerenciamento flexível de comandos
- Suporte a múltiplos tipos de tarefas

## Melhorias em relação à v7

1. **Interface Moderna com Tema Escuro**
   - Design moderno e elegante com tema escuro
   - Hierarquia visual e legibilidade aprimoradas
   - Componentes de UI modernos com estilo personalizado
   - Sistema de logs integrado com controle de visibilidade

2. **Arquitetura Modular Aprimorada**
   - Organização clara de componentes e responsabilidades
   - Sistema de plugins para tarefas
   - Gerenciamento de estado e configurações melhorado
   - Melhor manutenção e extensibilidade do código

3. **Manuseio de Áudio Aprimorado**
   - Seleção avançada de dispositivos
   - Gerenciamento robusto de dispositivos de entrada/saída
   - Detecção de atividade de voz (VAD) aprimorada
   - Controle de velocidade de voz
   - Personalização de sotaque, entonação e emoção

## Estrutura do Projeto

```
junin_v8/
├── _pocs/                 # Provas de conceito e testes
├── config/               
│   ├── audio_config.py    # Configurações de áudio
│   ├── log_config.py      # Configurações de log
│   └── settings_manager.py # Gerenciador de configurações
├── handlers/
│   ├── audio_handler.py   # Manipulação de áudio
│   ├── chat_handler.py    # Manipulação de chat
│   ├── event_handlers.py  # Manipulação de eventos
│   └── speech_handler.py  # Manipulação de fala
├── modules/
│   ├── anthropic/         # Módulos de integração Anthropic
│   │   └── computer_control/
│   ├── ollama/           # Módulos de integração Ollama
│   │   └── chat/
│   └── open_ai/          # Módulos de integração OpenAI
│       ├── chat/         # Chat completions
│       ├── chat_realtime/ # Chat em tempo real
│       ├── stt/          # Speech to Text
│       └── tts/          # Text to Speech
├── prompts/              # Templates de prompts
├── tasks_folder/         # Tarefas dinâmicas
├── ui/
│   ├── app_layout.py     # Layout principal
│   ├── components.py     # Componentes de UI
│   ├── theme.py         # Configurações de tema
│   └── imgs/            # Recursos de imagem
├── app.py               # Aplicação principal
├── junin_settings.json  # Configurações do aplicativo
└── requirements.txt     # Dependências do projeto
```

## Recursos

- Interface moderna com tema escuro
- Interação por voz com suporte a VAD
- Múltiplos motores TTS (OpenAI e local)
- Múltiplos backends de chat (OpenAI e Ollama)
- Seleção de dispositivo de áudio
- Automação de computador via Anthropic
- Sistema de tarefas dinâmico
- Configurações personalizáveis:
  - Velocidade de voz
  - Sotaque
  - Entonação
  - Emoção
  - Idioma
  - Modelo de chat GPT
  - Motor de voz
  - Configurações de monitor
- Sistema de logs integrado
- Transcrição em tempo real (online/offline)
- Correção ortográfica
- Suporte a teclas de atalho globais

## Requisitos

- Python 3.8+
- Chave da API OpenAI
- Chave da API Anthropic (para automação de computador)
- Bibliotecas de áudio em nível de sistema
- Dependências listadas em requirements.txt:
  - openai>=1.0.0
  - python-dotenv>=0.19.0
  - Pillow>=9.0.0
  - PyAudio>=0.2.11
  - keyboard>=0.13.5
  - numpy>=1.21.0
  - pyttsx3>=2.90
  - whisper>=1.0.0 (opcional para transcrição local)
  - scipy>=1.7.0

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

2. Recursos disponíveis:
   - Selecione dispositivos de áudio de entrada e saída
   - Configure velocidade, sotaque, entonação e emoção da voz
   - Escolha entre diferentes modelos de chat GPT
   - Alterne entre transcrição online/offline
   - Ative/desative o sistema de logs
   - Configure índice e offset do monitor
   - Ative/desative fala do computador
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
