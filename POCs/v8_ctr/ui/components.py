import tkinter as tk
from tkinter import ttk
import json
import os
from ui.theme import DarkTheme

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
            spacing3=1,
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
        # Configura as tags com os novos estilos e margem inferior
        self.tag_config("user", background=DarkTheme.USER_MESSAGE_BG, font=('Arial', 8, 'italic'), justify='left', spacing3=1)
        self.tag_config("Junin", background=DarkTheme.BOT_MESSAGE_BG, font=('Arial', 11, 'bold'), justify='left', spacing3=1)

    def extract_message_text(self, message):
        """Extrai o texto da mensagem do JSON se necessário."""
        try:
            # Se a mensagem começa com aspas triplas e 'json', remove isso
            if isinstance(message, str):
                message = message.replace('```json\n', '').replace('\n```', '')
                if message.strip().startswith('{'):
                    data = json.loads(message)
                    if isinstance(data, dict):
                        if 'content' in data and isinstance(data['content'], dict):
                            return data['content'].get('answer', '')
                        elif 'answer' in data:
                            return data['answer']
            return message
        except:
            return message

    def add_message(self, message, sender):
        """Adiciona uma mensagem à exibição do chat com a formatação apropriada."""
        if self.get("1.0", tk.END).strip():
            self.insert(tk.END, "\n")  # Apenas uma quebra de linha
        
        # Processa a mensagem se for do Junin
        if sender == "Junin":
            message = self.extract_message_text(message)
        
        # Adiciona a mensagem ao chat com margem inferior através da tag
        self.insert(tk.END, f"{sender}: {message}", sender)
        self.see(tk.END)

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
