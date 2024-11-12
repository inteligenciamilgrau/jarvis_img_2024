class DarkTheme:
    # Cores principais
    BG_PRIMARY = "#1E1E1E"
    BG_SECONDARY = "#252526"
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#CCCCCC"
    
    # Cores de destaque
    ACCENT_PRIMARY = "#007ACC"
    ACCENT_SECONDARY = "#0098FF"
    ACCENT_ERROR = "#FF3333"
    
    # Cores dos botões
    BUTTON_BG = "#2D2D2D"
    BUTTON_BG_HOVER = "#3D3D3D"
    BUTTON_BG_ACTIVE = "#007ACC"
    BUTTON_TEXT = "#FFFFFF"
    
    # Cores da área de entrada/texto
    INPUT_BG = "#2D2D2D"
    INPUT_TEXT = "#FFFFFF"
    INPUT_BORDER = "#3D3D3D"
    
    # Cores de exibição do chat
    CHAT_BG = "#252526"
    CHAT_TEXT = "#FFFFFF"
    USER_MESSAGE_BG = "#2D2D2D"
    BOT_MESSAGE_BG = "#3D3D3D"

class AudioConfig:
    CHUNK = 1024
    FORMAT = 8  # pyaudio.paInt16
    CHANNELS = 1
    RATE = 24000
    MOVING_AVERAGE_WINDOW = 50
    VOLUME_MULTIPLIER = 3
    NOISE_FLOOR = 100
    RECORD_TIME_AFTER_DETECTION = 2.0
    DETECTION_TIME = 0.2
