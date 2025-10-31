from abc import ABC, abstractmethod

class Caballo(ABC):
    def __init__(self, nombre: str, raza: str, velocidad: float, energia: float, resistencia: float):
        self.nombre = nombre
        self.raza = raza
        self.velocidad = velocidad
        self.__energia = energia
        self.resistencia = resistencia
        self.vivo = True

    @property
    def energia(self) -> float:
        return self.__energia

    @energia.setter
    def energia(self, value: float):
        self.__energia = max(0.0, min(100.0, value))

    @abstractmethod
    def bonificacion_terreno(self, clima: str) -> float:
        ...

    def consumir_energia(self, cantidad: float):
        self.energia -= max(0.0, cantidad / max(0.1, self.resistencia))

    def recuperar_energia(self, cantidad: float):
        self.energia += cantidad


class Yegua(Caballo):
    def __init__(self, nombre: str):
        super().__init__(nombre, "Yegua", velocidad=8.0, energia=100.0, resistencia=1.2)

    def bonificacion_terreno(self, clima: str) -> float:
        if clima == "Barro":
            return 1.05
        if clima == "Ventoso":
            return 0.97
        return 1.0


class PuraSangre(Caballo):
    def __init__(self, nombre: str):
        super().__init__(nombre, "Pura Sangre", velocidad=9.5, energia=100.0, resistencia=0.9)

    def bonificacion_terreno(self, clima: str) -> float:
        if clima == "Lluvioso":
            return 0.94
        if clima == "Soleado":
            return 1.06
        return 1.0
