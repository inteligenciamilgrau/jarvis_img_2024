import tkinter as tk
from tkinter import ttk
import json
import os
from config.theme import DarkTheme

class ModernButton(tk.Button):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            bg=DarkTheme.BUTTON_BG,
            fg=DarkTheme.BUTTON_TEXT,
            activebackground=DarkTheme.BUTTON_BG_HOVER,
            activeforeground=DarkTheme.BUTTON_TEXT,
            relief=tk.FLAT,
            cursor="hand2",
            **kwargs
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self.config(bg=DarkTheme.BUTTON_BG_HOVER)

    def _on_leave(self, e):
        self.config(bg=DarkTheme.BUTTON_BG)

class ModernTextArea(tk.Text):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            bg=DarkTheme.INPUT_BG,
            fg=DarkTheme.INPUT_TEXT,
            insertbackground=DarkTheme.TEXT_PRIMARY,
            selectbackground=DarkTheme.ACCENT_PRIMARY,
            selectforeground=DarkTheme.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=10,
            pady=5,
            spacing1=0,  # Remove espaço entre linhas
            **kwargs
        )

class ModernFrame(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            bg=DarkTheme.BG_SECONDARY,
            **kwargs
        )

class ModernCheckbutton(tk.Checkbutton):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            selectcolor=DarkTheme.BG_PRIMARY,
            activebackground=DarkTheme.BG_SECONDARY,
            activeforeground=DarkTheme.TEXT_PRIMARY,
            **kwargs
        )

class ModernOptionMenu(tk.OptionMenu):
    def __init__(self, master, variable, *values, **kwargs):
        super().__init__(
            master,
            variable,
            *values,
            **kwargs
        )
        self.config(
            bg=DarkTheme.BUTTON_BG,
            fg=DarkTheme.TEXT_PRIMARY,
            activebackground=DarkTheme.BUTTON_BG_HOVER,
            activeforeground=DarkTheme.TEXT_PRIMARY,
            relief=tk.FLAT,
            cursor="hand2",
            highlightthickness=0
        )
        self["menu"].config(
            bg=DarkTheme.BG_SECONDARY,
            fg=DarkTheme.TEXT_PRIMARY,
            activebackground=DarkTheme.ACCENT_PRIMARY,
            activeforeground=DarkTheme.TEXT_PRIMARY,
            relief=tk.FLAT
        )

class ChatDisplay(ModernTextArea):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # Configura as tags com os novos estilos
        self.tag_config("user", background=DarkTheme.USER_MESSAGE_BG, font=('Arial', 8, 'italic'), justify='left')
        self.tag_config("Junin", background=DarkTheme.BOT_MESSAGE_BG, font=('Arial', 11, 'bold'), justify='left')

    def add_message(self, message, sender):
        """Adiciona uma mensagem à exibição do chat com a formatação apropriada."""
        if self.get("1.0", tk.END).strip():
            self.insert(tk.END, "\n")
        
        tag = "user" if sender == "Eu" else "Junin"
        self.insert(tk.END, f"{sender}: {message}", tag)  # Removido \n do final
        
        self.see(tk.END)

class SettingsManager:
    def __init__(self, settings_file):
        self.settings_file = settings_file
        self.settings = self.load_settings()

    def load_settings(self):
        """Carrega as configurações do arquivo."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                print("Erro ao carregar o arquivo de configurações")
                return {}
        return {}

    def save_settings(self, settings):
        """Salva as configurações no arquivo."""
        try:
            with open(self.settings_file, 'w') as file:
                json.dump(settings, file)
        except Exception as e:
            print(f"Erro ao salvar as configurações: {e}")

    def get_setting(self, key, default=None):
        """Obtém o valor de uma configuração."""
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        """Define um valor de configuração e salva.""" 
        self.settings[key] = value
        self.save_settings(self.settings)

# Novo Seletor de Combo para o Modelo ChatGPT
class ChatGPTModelSelector(ModernOptionMenu):
    def __init__(self, master, variable):
        models = [
            "gpt-4o", "gpt-4o-2024-05-13", "gpt-4o-2024-08-06",
            "chatgpt-4o-latest", "gpt-4o-mini", "gpt-4o-mini-2024-07-18",
            "o1-preview", "o1-preview-2024-09-12", "o1-mini",
            "o1-mini-2024-09-12", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"
        ]
        super().__init__(master, variable, *models)
