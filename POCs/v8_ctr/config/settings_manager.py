

class SettingsManager:
    def __init__(self, settings_file):
        self.settings_file = settings_file
        self.settings = self.load_settings()

    def load_settings(self):
        """Carrega as configurações do arquivo."""
        try:
            with open(self.settings_file, 'r') as f:
                import json
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_settings(self, settings):
        """Salva as configurações no arquivo."""
        with open(self.settings_file, 'w') as f:
            import json
            json.dump(settings, f, indent=4)

    def get_setting(self, key, default=None):
        """Obtém uma configuração específica."""
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        """Define uma configuração específica."""
        self.settings[key] = value
        self.save_settings(self.settings)

    def save_window_geometry(self, geometry):
        """Salva a geometria da janela nas configurações."""
        self.set_setting('window_geometry', geometry)

    def get_window_geometry(self):
        """Obtém a geometria da janela salva."""
        return self.get_setting('window_geometry', '1100x700+560+100')
