"""Nodos del árbol de sintaxis abstracta de Avadia 1.0."""
from dataclasses import dataclass
from typing import Any


class Nodo:
    pass


@dataclass
class Programa(Nodo):
    instrucciones: list


@dataclass
class Literal(Nodo):
    valor: Any


@dataclass
class Variable(Nodo):
    nombre: str


@dataclass
class ListaLiteral(Nodo):
    elementos: list


@dataclass
class AccesoIndice(Nodo):
    objeto: Nodo
    indice: Nodo


@dataclass
class Llamada(Nodo):
    funcion: Nodo
    argumentos: list


@dataclass
class OperacionUnaria(Nodo):
    operador: str
    operando: Nodo


@dataclass
class OperacionBinaria(Nodo):
    izquierda: Nodo
    operador: str
    derecha: Nodo


@dataclass
class CrearVariable(Nodo):
    nombre: str
    valor: Nodo
    tipo: str = None


@dataclass
class AsignarVariable(Nodo):
    nombre: str
    valor: Nodo


@dataclass
class Mostrar(Nodo):
    expresion: Nodo


@dataclass
class ExpresionSentencia(Nodo):
    expresion: Nodo


@dataclass
class Condicional(Nodo):
    condicion: Nodo
    entonces: list
    sino: list


@dataclass
class Mientras(Nodo):
    condicion: Nodo
    cuerpo: list


@dataclass
class Para(Nodo):
    nombre: str
    iterable: Nodo
    cuerpo: list


@dataclass
class Funcion(Nodo):
    nombre: str
    parametros: list
    cuerpo: list


@dataclass
class Retornar(Nodo):
    expresion: Nodo | None


@dataclass
class Romper(Nodo):
    pass


@dataclass
class Importar(Nodo):
    ruta: Nodo


@dataclass
class Ayuda(Nodo):
    pass


@dataclass
class DiccionarioLiteral(Nodo):
    pares: list


@dataclass
class AsignarIndice(Nodo):
    objeto: Nodo
    indice: Nodo
    valor: Nodo
