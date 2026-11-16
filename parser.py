"""Analizador sintáctico de Avadia 1.3."""
from lexer import Token
from ast_nodos import *
from nucleo.errores import ErrorSintactico
from nucleo.tipos import TIPOS


class Parser:
    CIERRES = {"FIN", "SINO"}

    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0

    def _actual(self):
        return self.tokens[min(self.posicion, len(self.tokens) - 1)]

    def _avanzar(self):
        t = self._actual()
        if t.tipo != "FIN_ARCHIVO":
            self.posicion += 1
        return t

    def _aceptar(self, *tipos):
        if self._actual().tipo in tipos:
            return self._avanzar()
        return None

    def _esperar(self, tipo, mensaje=None):
        t = self._actual()
        if t.tipo != tipo:
            detalle = mensaje or f"Se esperaba {tipo}, pero se encontró {t.tipo}"
            raise ErrorSintactico(f"{detalle} en línea {t.linea}, columna {t.columna}")
        return self._avanzar()

    def _saltos(self):
        while self._aceptar("NUEVA_LINEA"):
            pass

    def analizar(self):
        instrucciones = []
        self._saltos()
        while self._actual().tipo != "FIN_ARCHIVO":
            if self._actual().tipo in ("FIN", "SINO"):
                t = self._actual()
                raise ErrorSintactico(f"'{t.valor}' inesperado en línea {t.linea}, columna {t.columna}")
            instrucciones.append(self._instruccion())
            if self._actual().tipo not in ("NUEVA_LINEA", "FIN_ARCHIVO"):
                t = self._actual()
                raise ErrorSintactico(f"Se esperaba un salto de línea en línea {t.linea}, columna {t.columna}")
            self._saltos()
        return Programa(instrucciones)

    def _instruccion(self):
        t = self._actual()
        nodo = self._instruccion_base()
        nodo.linea = t.linea
        nodo.columna = t.columna
        return nodo

    def _instruccion_base(self):
        tipo = self._actual().tipo
        if tipo == "CREAR": return self._crear()
        if tipo == "MOSTRAR": return self._mostrar()
        if tipo == "SI": return self._condicional()
        if tipo == "MIENTRAS": return self._mientras()
        if tipo == "PARA": return self._para()
        if tipo == "FUNCION": return self._funcion()
        if tipo == "RETORNAR": return self._retornar()
        if tipo == "ROMPER":
            self._avanzar(); return Romper()
        if tipo == "IMPORTAR": return self._importar()
        if tipo == "AYUDA":
            self._avanzar(); return Ayuda()
        if tipo == "IDENTIFICADOR" and self.tokens[min(self.posicion + 1, len(self.tokens)-1)].tipo == "IGUAL":
            return self._asignar()
        if tipo == "IDENTIFICADOR":
            expresion = self._expresion()
            if self._aceptar("IGUAL"):
                if not isinstance(expresion, AccesoIndice):
                    t = self._actual()
                    raise ErrorSintactico(f"Solo se puede asignar a variables o a elementos de listas y diccionarios en línea {t.linea}, columna {t.columna}")
                return AsignarIndice(expresion.objeto, expresion.indice, self._expresion())
            return ExpresionSentencia(expresion)
        t = self._actual()
        raise ErrorSintactico(f"Instrucción no reconocida {t.valor!r} en línea {t.linea}, columna {t.columna}")

    def _crear(self):
        self._esperar("CREAR")
        n = self._esperar("IDENTIFICADOR", "Se esperaba un nombre para la variable")
        tipo = None
        if self._aceptar("DOS_PUNTOS"):
            t = self._actual()
            tipo = self._esperar("IDENTIFICADOR", "Se esperaba el nombre de un tipo después de ':'").valor
            if tipo not in TIPOS:
                raise ErrorSintactico(f"Tipo desconocido '{tipo}' en línea {t.linea}, columna {t.columna}",
                                      sugerencia="Tipos disponibles: " + ", ".join(TIPOS))
        self._esperar("IGUAL", "Se esperaba '=' al crear la variable")
        return CrearVariable(n.valor, self._expresion(), tipo)

    def _asignar(self):
        n = self._esperar("IDENTIFICADOR")
        self._esperar("IGUAL")
        return AsignarVariable(n.valor, self._expresion())

    def _mostrar(self):
        self._esperar("MOSTRAR")
        return Mostrar(self._expresion())

    def _exigir_salto_bloque(self, palabra):
        if self._actual().tipo != "NUEVA_LINEA":
            t = self._actual()
            raise ErrorSintactico(f"Se esperaba un salto de línea después de '{palabra}' en línea {t.linea}, columna {t.columna}")
        self._saltos()

    def _bloque(self, cierres):
        instrucciones = []
        while self._actual().tipo not in cierres:
            if self._actual().tipo == "FIN_ARCHIVO":
                t = self._actual()
                nombres = " o ".join(c.lower() for c in sorted(cierres))
                raise ErrorSintactico(f"Bloque sin cerrar; se esperaba {nombres} en línea {t.linea}, columna {t.columna}")
            instrucciones.append(self._instruccion())
            if self._actual().tipo not in ("NUEVA_LINEA",) and self._actual().tipo not in cierres:
                t = self._actual()
                raise ErrorSintactico(f"Se esperaba un salto de línea dentro del bloque en línea {t.linea}, columna {t.columna}")
            self._saltos()
        return instrucciones

    def _condicional(self):
        self._esperar("SI")
        condicion = self._expresion()
        self._esperar("ENTONCES", "Se esperaba 'entonces' después de la condición")
        self._exigir_salto_bloque("entonces")
        entonces = self._bloque({"SINO", "FIN"})
        sino = []
        if self._aceptar("SINO"):
            self._exigir_salto_bloque("sino")
            sino = self._bloque({"FIN"})
        self._esperar("FIN", "Se esperaba 'fin' para cerrar el condicional")
        return Condicional(condicion, entonces, sino)

    def _mientras(self):
        self._esperar("MIENTRAS")
        condicion = self._expresion()
        self._esperar("HACER", "Se esperaba 'hacer' después de la condición")
        self._exigir_salto_bloque("hacer")
        cuerpo = self._bloque({"FIN"})
        self._esperar("FIN", "Se esperaba 'fin' para cerrar mientras")
        return Mientras(condicion, cuerpo)

    def _para(self):
        self._esperar("PARA")
        nombre = self._esperar("IDENTIFICADOR", "Se esperaba una variable de control")
        self._esperar("EN", "Se esperaba 'en' después de la variable de control")
        iterable = self._expresion()
        self._esperar("HACER", "Se esperaba 'hacer' después del iterable")
        self._exigir_salto_bloque("hacer")
        cuerpo = self._bloque({"FIN"})
        self._esperar("FIN", "Se esperaba 'fin' para cerrar para")
        return Para(nombre.valor, iterable, cuerpo)

    def _funcion(self):
        self._esperar("FUNCION")
        nombre = self._esperar("IDENTIFICADOR", "Se esperaba el nombre de la función")
        self._esperar("ABRIR_PAREN", "Se esperaba '(' después del nombre de la función")
        parametros = []
        if self._actual().tipo != "CERRAR_PAREN":
            while True:
                p = self._esperar("IDENTIFICADOR", "Se esperaba el nombre de un parámetro")
                if p.valor in parametros:
                    raise ErrorSintactico(f"Parámetro repetido: {p.valor}")
                parametros.append(p.valor)
                if not self._aceptar("COMA"):
                    break
        self._esperar("CERRAR_PAREN", "Se esperaba ')' después de los parámetros")
        self._exigir_salto_bloque("declaración de función")
        cuerpo = self._bloque({"FIN"})
        self._esperar("FIN", "Se esperaba 'fin' para cerrar la función")
        return Funcion(nombre.valor, parametros, cuerpo)

    def _retornar(self):
        self._esperar("RETORNAR")
        if self._actual().tipo in ("NUEVA_LINEA", "FIN", "SINO", "FIN_ARCHIVO"):
            return Retornar(None)
        return Retornar(self._expresion())

    def _importar(self):
        self._esperar("IMPORTAR")
        return Importar(self._expresion())

    # Precedencia: o, y, no, comparación/pertenencia, suma, producto, unarios.
    def _expresion(self): return self._o()

    def _o(self):
        nodo = self._y()
        while self._aceptar("O"):
            nodo = OperacionBinaria(nodo, "o", self._y())
        return nodo

    def _y(self):
        nodo = self._no()
        while self._aceptar("Y"):
            nodo = OperacionBinaria(nodo, "y", self._no())
        return nodo

    def _no(self):
        if self._aceptar("NO"):
            return OperacionUnaria("no", self._no())
        return self._comparacion()

    def _comparacion(self):
        nodo = self._suma()
        operadores = {"IGUAL_IGUAL": "==", "DIFERENTE": "!=", "MENOR": "<", "MAYOR": ">", "MENOR_IGUAL": "<=", "MAYOR_IGUAL": ">=", "EN": "en"}
        while self._actual().tipo in operadores:
            operador = operadores[self._avanzar().tipo]
            nodo = OperacionBinaria(nodo, operador, self._suma())
        return nodo

    def _suma(self):
        nodo = self._producto()
        while self._actual().tipo in ("MAS", "MENOS"):
            operador = "+" if self._avanzar().tipo == "MAS" else "-"
            nodo = OperacionBinaria(nodo, operador, self._producto())
        return nodo

    def _producto(self):
        nodo = self._unario()
        while self._actual().tipo in ("MULTIPLICAR", "DIVIDIR", "MODULO"):
            tipo = self._avanzar().tipo
            operador = {"MULTIPLICAR": "*", "DIVIDIR": "/", "MODULO": "%"}[tipo]
            nodo = OperacionBinaria(nodo, operador, self._unario())
        return nodo

    def _unario(self):
        if self._aceptar("MENOS"): return OperacionUnaria("-", self._unario())
        if self._aceptar("MAS"): return OperacionUnaria("+", self._unario())
        return self._postfijo()

    def _postfijo(self):
        nodo = self._primario()
        while True:
            if self._aceptar("ABRIR_PAREN"):
                argumentos = []
                if self._actual().tipo != "CERRAR_PAREN":
                    while True:
                        argumentos.append(self._expresion())
                        if not self._aceptar("COMA"):
                            break
                self._esperar("CERRAR_PAREN", "Se esperaba ')' al cerrar la llamada")
                nodo = Llamada(nodo, argumentos)
            elif self._aceptar("ABRIR_CORCHETE"):
                indice = self._expresion()
                self._esperar("CERRAR_CORCHETE", "Se esperaba ']' al cerrar el índice")
                nodo = AccesoIndice(nodo, indice)
            else:
                return nodo

    def _primario(self):
        t = self._actual()
        if t.tipo in ("NUMERO", "TEXTO", "BOOLEANO"):
            self._avanzar(); return Literal(t.valor)
        if t.tipo == "IDENTIFICADOR":
            self._avanzar(); return Variable(t.valor)
        if self._aceptar("ABRIR_PAREN"):
            nodo = self._expresion()
            self._esperar("CERRAR_PAREN", "Falta ')' para cerrar la expresión")
            return nodo
        if self._aceptar("ABRIR_CORCHETE"):
            elementos = []
            self._saltos()
            if self._actual().tipo != "CERRAR_CORCHETE":
                while True:
                    self._saltos()
                    elementos.append(self._expresion())
                    self._saltos()
                    if not self._aceptar("COMA"):
                        break
            self._saltos()
            self._esperar("CERRAR_CORCHETE", "Falta ']' para cerrar la lista")
            return ListaLiteral(elementos)
        if self._aceptar("LLAVE_ABRIR"):
            pares = []
            self._saltos()
            if self._actual().tipo != "LLAVE_CERRAR":
                while True:
                    self._saltos()
                    clave = self._expresion()
                    self._saltos()
                    self._esperar("DOS_PUNTOS", "Se esperaba ':' entre la clave y el valor del diccionario")
                    self._saltos()
                    pares.append((clave, self._expresion()))
                    self._saltos()
                    if not self._aceptar("COMA"):
                        break
            self._saltos()
            self._esperar("LLAVE_CERRAR", "Falta '}' para cerrar el diccionario")
            return DiccionarioLiteral(pares)
        raise ErrorSintactico(f"Se esperaba un valor o expresión; se encontró {t.tipo} en línea {t.linea}, columna {t.columna}")
