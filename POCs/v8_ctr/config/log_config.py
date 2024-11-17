import logging

class LogConfig:
    """
    # Classe para gerenciar a configuração de logs do sistema
    """
    _instance = None
    _show_logs = False
    
    @classmethod
    def get_instance(cls):
        """Retorna a instância única da classe (Singleton)"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_log_visibility(self, show_logs: bool):
        """
        # Define se os logs devem ser exibidos ou não
        Args:
            show_logs (bool): True para exibir logs, False para ocultar
        """
        self._show_logs = show_logs
        
        # Configura o nível de log baseado na visibilidade
        log_level = logging.INFO if show_logs else logging.WARNING
        logging.getLogger().setLevel(log_level)
        
    def is_showing_logs(self) -> bool:
        """
        # Retorna se os logs estão sendo exibidos
        Returns:
            bool: True se os logs estão visíveis, False caso contrário
        """
        return self._show_logs
