"""Analizador léxico de Avadia 1.3."""
from dataclasses import dataclass
from typing import Any

from nucleo.errores import ErrorLexico


@dataclass(frozen=True)
class Token:
    tipo: str
    valor: Any
    linea: int
    columna: int

    def __repr__(self):
        return f"Token({self.tipo}, {self.valor!r}, línea={self.linea}, columna={self.columna})"


class Lexer:
    PALABRAS = {
        "crear": "CREAR", "mostrar": "MOSTRAR", "si": "SI",
        "entonces": "ENTONCES", "sino": "SINO", "fin": "FIN",
        "verdadero": "BOOLEANO", "falso": "BOOLEANO",
        "y": "Y", "o": "O", "no": "NO", "en": "EN",
        "mientras": "MIENTRAS", "hacer": "HACER", "para": "PARA",
        "romper": "ROMPER", "funcion": "FUNCION", "retornar": "RETORNAR",
        "importar": "IMPORTAR", "ayuda": "AYUDA",
    }
    OPERADORES = {
        "=": "IGUAL", "==": "IGUAL_IGUAL", "!=": "DIFERENTE",
        "<": "MENOR", ">": "MAYOR", "<=": "MENOR_IGUAL", ">=": "MAYOR_IGUAL",
        "+": "MAS", "-": "MENOS", "*": "MULTIPLICAR", "/": "DIVIDIR", "%": "MODULO",
    }
    SIMBOLOS = {
        "(": "ABRIR_PAREN", ")": "CERRAR_PAREN",
        "[": "ABRIR_CORCHETE", "]": "CERRAR_CORCHETE",
        ",": "COMA", "{": "LLAVE_ABRIR", "}": "LLAVE_CERRAR", ":": "DOS_PUNTOS",
    }
    ESCAPES = {"n": "\n", "t": "\t", '"': '"', "'": "'", "\\": "\\"}

    def __init__(self, codigo: str):
        self.codigo = codigo
        self.posicion = 0
        self.linea = 1
        self.columna = 1
        self.tokens = []

    def _actual(self, desplazamiento=0):
        indice = self.posicion + desplazamiento
        return self.codigo[indice] if indice < len(self.codigo) else None

    def _avanzar(self):
        c = self._actual()
        if c is None:
            return None
        if c == "\r":
            self.posicion += 1
            if self._actual() == "\n":
                self.posicion += 1
            self.linea += 1
            self.columna = 1
            return "\n"
        self.posicion += 1
        if c == "\n":
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1
        return c

    def _agregar(self, tipo, valor, linea, columna):
        self.tokens.append(Token(tipo, valor, linea, columna))

    def _leer_palabra(self):
        linea, columna = self.linea, self.columna
        inicio = self.posicion
        while (c := self._actual()) is not None and (c.isalnum() or c == "_"):
            self._avanzar()
        palabra = self.codigo[inicio:self.posicion]
        tipo = self.PALABRAS.get(palabra, "IDENTIFICADOR")
        valor = True if palabra == "verdadero" else False if palabra == "falso" else palabra
        self._agregar(tipo, valor, linea, columna)

    def _leer_numero(self):
        linea, columna = self.linea, self.columna
        inicio = self.posicion
        while (c := self._actual()) is not None and c.isdigit():
            self._avanzar()
        decimal = self._actual() == "." and (self._actual(1) or "").isdigit()
        if decimal:
            self._avanzar()
            while (c := self._actual()) is not None and c.isdigit():
                self._avanzar()
        bruto = self.codigo[inicio:self.posicion]
        self._agregar("NUMERO", float(bruto) if decimal else int(bruto), linea, columna)

    def _leer_texto(self):
        linea0, columna0 = self.linea, self.columna
        comilla = self._avanzar()
        partes = []
        while True:
            c = self._actual()
            if c is None:
                raise ErrorLexico(f"Texto sin cerrar; comenzó en línea {linea0}, columna {columna0}")
            if c in ("\n", "\r"):
                raise ErrorLexico(f"Salto de línea dentro de texto en línea {self.linea}, columna {self.columna}")
            if c == comilla:
                self._avanzar()
                break
            if c == "\\":
                self._avanzar()
                e = self._actual()
                if e is None or e not in self.ESCAPES:
                    raise ErrorLexico(f"Secuencia de escape no válida en línea {self.linea}, columna {self.columna}")
                partes.append(self.ESCAPES[e])
                self._avanzar()
            else:
                partes.append(self._avanzar())
        self._agregar("TEXTO", "".join(partes), linea0, columna0)

    def tokenizar(self):
        while (c := self._actual()) is not None:
            if c in " \t\f":
                self._avanzar()
                continue
            if c in "\r\n":
                linea, columna = self.linea, self.columna
                self._avanzar()
                self._agregar("NUEVA_LINEA", "\n", linea, columna)
                continue
            if c == "/" and self._actual(1) == "/":
                while self._actual() not in (None, "\n", "\r"):
                    self._avanzar()
                continue
            if c.isalpha() or c == "_":
                self._leer_palabra()
                continue
            if c.isdigit():
                self._leer_numero()
                continue
            if c in ('"', "'"):
                self._leer_texto()
                continue
            linea, columna = self.linea, self.columna
            doble = c + (self._actual(1) or "")
            if doble in self.OPERADORES:
                self._avanzar(); self._avanzar()
                self._agregar(self.OPERADORES[doble], doble, linea, columna)
                continue
            if c in self.OPERADORES:
                self._avanzar()
                self._agregar(self.OPERADORES[c], c, linea, columna)
                continue
            if c in self.SIMBOLOS:
                self._avanzar()
                self._agregar(self.SIMBOLOS[c], c, linea, columna)
                continue
            raise ErrorLexico(f"Carácter inesperado {c!r} en línea {linea}, columna {columna}")
        self._agregar("FIN_ARCHIVO", None, self.linea, self.columna)
        return self.tokens
