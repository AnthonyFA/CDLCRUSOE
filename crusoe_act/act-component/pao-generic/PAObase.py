from abc import ABC, abstractmethod

class PAOBase(ABC):
    """Interface for the development of PAOs"""
    
    def __init__(self, name: str):
        self.name = name  # name or ID of the element we are creating/connecting
    
    @abstractmethod
    def execute(self, action: str, target: str) -> bool:
        """
        
        Ejecuta una acción sobre el elemento de defensa activa.
        `action` podría ser por ejemplo "block" o "unblock" (u otras acciones definidas),
        y `target` es la entidad objetivo (IP, dominio, user ID, etc.).
        Retorna True si la acción se realizó con éxito, False en caso contrario.
        """
        pass
    
    @abstractmethod
    def validate(self, action: str, target: str) -> bool:
        """
        Valida si la acción dada puede ejecutarse sobre el target.
        Comprueba formato, soportabilidad y cualquier condición de preejecución.
        Retorna True si es válido; False o lanza excepción si no lo es.
        """
        pass
    
    @abstractmethod
    def get_status(self) -> dict:
        """
        Obtiene el estado actual del PAO, incluyendo disponibilidad (health),
        capacidad (máxima y utilizada) y cualquier otra métrica relevante.
        Retorna un diccionario (u objeto) con esta información.
        """
        pass
