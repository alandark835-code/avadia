"""Intérprete seguro de Avadia 1.3. No utiliza eval() ni exec()."""
from pathlib import Path

from ast_nodos import (
    Programa, Literal, Variable, ListaLiteral, AccesoIndice, Llamada,
    OperacionUnaria, OperacionBinaria, CrearVariable, AsignarVariable,
    Mostrar, ExpresionSentencia, Condicional, Mientras, Para, Funcion,
    Retornar, Romper, Importar, Ayuda, DiccionarioLiteral, AsignarIndice,
)
from lexer import Lexer
from parser import Parser
from nucleo.errores import ErrorLexico, ErrorSintactico, ErrorEjecucion
from nucleo.registro import RegistroBibliotecas, FuncionNativa, ErrorRegistro
from nucleo.tipos import cumple, nombre_de_valor, TIPOS
from bibliotecas.juego2d import Motor2D, ErrorJuego2D
from bibliotecas.web import CreadorWeb, ErrorWeb
from bibliotecas.archivos import BibliotecaArchivos, ErrorArchivo
from bibliotecas.sprites import ErrorSprite
from bibliotecas.audio import ErrorAudio
from bibliotecas.mapas import Mapa, ErrorMapa
from bibliotecas.fisica2d import ErrorFisica




class _RomperBucle(Exception):
    pass


class _RetornoFuncion(Exception):
    def __init__(self, valor):
        self.valor = valor


class Entorno:
    def __init__(self, padre=None):
        self.valores = {}
        self.tipos = {}
        self.padre = padre

    def definir(self, nombre, valor, tipo=None):
        self.valores[nombre] = valor
        if tipo is not None:
            self.tipos[nombre] = tipo
        else:
            self.tipos.pop(nombre, None)

    def tipo_de(self, nombre):
        if nombre in self.valores:
            return self.tipos.get(nombre)
        if self.padre is not None:
            return self.padre.tipo_de(nombre)
        return None

    def obtener(self, nombre):
        if nombre in self.valores:
            return self.valores[nombre]
        if self.padre is not None:
            return self.padre.obtener(nombre)
        raise ErrorEjecucion(f"La variable '{nombre}' no existe",
                             sugerencia="Crea la variable con 'crear' antes de usarla")

    def asignar(self, nombre, valor):
        if nombre in self.valores:
            tipo = self.tipos.get(nombre)
            if not cumple(valor, tipo):
                raise ErrorEjecucion(f"La variable '{nombre}' es de tipo {tipo}, pero se intentó asignar {nombre_de_valor(valor)}",
                                     sugerencia=f"Usa un valor de tipo {tipo} o declara la variable sin tipo")
            self.valores[nombre] = valor
            return
        if self.padre is not None and self.padre.contiene(nombre):
            self.padre.asignar(nombre, valor)
            return
        raise ErrorEjecucion(f"No se puede modificar '{nombre}': la variable no existe")

    def contiene(self, nombre):
        return nombre in self.valores or (self.padre is not None and self.padre.contiene(nombre))


class FuncionAvadia:
    def __init__(self, declaracion, cierre):
        self.declaracion = declaracion
        self.cierre = cierre


class Interprete:
    MAX_ITERACIONES = 1_000_000

    def __init__(self, salida=print, entrada=input):
        self.salida = salida
        self.entrada = entrada
        self.entorno = Entorno()
        self.archivo_actual = None
        self.rutas_importadas = set()
        self.pila_importaciones = []
        self.juego2d = Motor2D()
        self.juego2d.al_colision = self._despachar_colision
        self.depurador = None
        self.pila_llamadas = []
        self.registro = RegistroBibliotecas()
        self.bibliotecas_cargadas = set()
        self.creador_web = CreadorWeb()
        self._instalar_funciones_nativas()

    def _instalar_funciones_nativas(self):
        funciones = {
            "leer": FuncionNativa("leer", self._nativa_leer, 0, 1),
            "longitud": FuncionNativa("longitud", self._nativa_longitud, 1, 1),
            "agregar": FuncionNativa("agregar", self._nativa_agregar, 2, 2),
            "quitar": FuncionNativa("quitar", self._nativa_quitar, 1, 2),
            "rango": FuncionNativa("rango", self._nativa_rango, 1, 3),
            "texto": FuncionNativa("texto", self._nativa_texto, 1, 1),
            "numero": FuncionNativa("numero", self._nativa_numero, 1, 1),
            "tipo": FuncionNativa("tipo", self._nativa_tipo, 1, 1),
            # Biblioteca gráfica 2D
            "juego_ventana": FuncionNativa("juego_ventana", self._nativa_juego_ventana, 0, 3),
            "juego_limpiar": FuncionNativa("juego_limpiar", self._nativa_juego_limpiar, 0, 1),
            "juego_rectangulo": FuncionNativa("juego_rectangulo", self._nativa_juego_rectangulo, 5, 5),
            "juego_circulo": FuncionNativa("juego_circulo", self._nativa_juego_circulo, 4, 4),
            "juego_texto": FuncionNativa("juego_texto", self._nativa_juego_texto, 3, 5),
            "juego_tecla": FuncionNativa("juego_tecla", self._nativa_juego_tecla, 1, 1),
            "juego_iniciar": FuncionNativa("juego_iniciar", self._nativa_juego_iniciar, 1, 1),
            # Biblioteca para páginas web
            "web_iniciar": FuncionNativa("web_iniciar", self._nativa_web_iniciar, 0, 1),
            "web_titulo": FuncionNativa("web_titulo", self._nativa_web_titulo, 1, 1),
            "web_parrafo": FuncionNativa("web_parrafo", self._nativa_web_parrafo, 1, 1),
            "web_boton": FuncionNativa("web_boton", self._nativa_web_boton, 1, 2),
            "web_imagen": FuncionNativa("web_imagen", self._nativa_web_imagen, 1, 2),
            "web_estilo": FuncionNativa("web_estilo", self._nativa_web_estilo, 1, 1),
            "web_html": FuncionNativa("web_html", self._nativa_web_html, 1, 1),
            "web_guardar": FuncionNativa("web_guardar", self._nativa_web_guardar, 1, 1),
            "web_servidor": FuncionNativa("web_servidor", self._nativa_web_servidor, 0, 1),
            # Formularios e interactividad web (Avadia 1.2)
            "web_formulario_iniciar": FuncionNativa("web_formulario_iniciar", self._nativa_web_formulario_iniciar, 1, 1),
            "web_campo": FuncionNativa("web_campo", self._nativa_web_campo, 2, 5),
            "web_casilla": FuncionNativa("web_casilla", self._nativa_web_casilla, 2, 3),
            "web_formulario_enviar": FuncionNativa("web_formulario_enviar", self._nativa_web_formulario_enviar, 0, 1),
            "web_bloque_iniciar": FuncionNativa("web_bloque_iniciar", self._nativa_web_bloque_iniciar, 1, 1),
            "web_bloque_cerrar": FuncionNativa("web_bloque_cerrar", self._nativa_web_bloque_cerrar, 0, 0),
            "web_boton_accion": FuncionNativa("web_boton_accion", self._nativa_web_boton_accion, 3, 3),
            "web_componente": FuncionNativa("web_componente", self._nativa_web_componente, 2, 2),
            "web_usar": FuncionNativa("web_usar", self._nativa_web_usar, 2, 2),
            "web_menu": FuncionNativa("web_menu", self._nativa_web_menu, 1, 1),
            "web_tarjeta": FuncionNativa("web_tarjeta", self._nativa_web_tarjeta, 2, 3),
            # Recursos del proyecto
            "recurso": FuncionNativa("recurso", self._nativa_recurso, 1, 1),
            "recursos": FuncionNativa("recursos", self._nativa_recursos, 0, 0),
            # Biblioteca de archivos (restringida a la carpeta del proyecto)
            "archivo_leer": FuncionNativa("archivo_leer", self._nativa_archivo_leer, 1, 1),
            "archivo_escribir": FuncionNativa("archivo_escribir", self._nativa_archivo_escribir, 2, 2),
            "archivo_agregar": FuncionNativa("archivo_agregar", self._nativa_archivo_agregar, 2, 2),
            "archivo_existe": FuncionNativa("archivo_existe", self._nativa_archivo_existe, 1, 1),
            "carpeta_crear": FuncionNativa("carpeta_crear", self._nativa_carpeta_crear, 1, 1),
            "archivo_listar": FuncionNativa("archivo_listar", self._nativa_archivo_listar, 0, 1),
            "archivo_eliminar": FuncionNativa("archivo_eliminar", self._nativa_archivo_eliminar, 2, 2),
            # Sprites y animaciones (Avadia 1.2)
            "sprite_cargar": FuncionNativa("sprite_cargar", self._nativa_sprite_cargar, 1, 3),
            "sprite_hoja": FuncionNativa("sprite_hoja", self._nativa_sprite_hoja, 3, 5),
            "sprite_mover": FuncionNativa("sprite_mover", self._nativa_sprite_mover, 3, 3),
            "sprite_posicion": FuncionNativa("sprite_posicion", self._nativa_sprite_posicion, 1, 1),
            "sprite_escala": FuncionNativa("sprite_escala", self._nativa_sprite_escala, 2, 2),
            "sprite_rotar": FuncionNativa("sprite_rotar", self._nativa_sprite_rotar, 2, 2),
            "sprite_capa": FuncionNativa("sprite_capa", self._nativa_sprite_capa, 2, 2),
            "sprite_eliminar": FuncionNativa("sprite_eliminar", self._nativa_sprite_eliminar, 1, 1),
            "animacion_crear": FuncionNativa("animacion_crear", self._nativa_animacion_crear, 3, 4),
            "animacion_reproducir": FuncionNativa("animacion_reproducir", self._nativa_animacion_reproducir, 2, 2),
            "animacion_pausar": FuncionNativa("animacion_pausar", self._nativa_animacion_pausar, 1, 1),
            "animacion_detener": FuncionNativa("animacion_detener", self._nativa_animacion_detener, 1, 1),
            "animacion_velocidad": FuncionNativa("animacion_velocidad", self._nativa_animacion_velocidad, 2, 2),
            # Física y colisiones (Avadia 1.2)
            "fisica_gravedad": FuncionNativa("fisica_gravedad", self._nativa_fisica_gravedad, 1, 1),
            "fisica_activar": FuncionNativa("fisica_activar", self._nativa_fisica_activar, 3, 5),
            "fisica_pared": FuncionNativa("fisica_pared", self._nativa_fisica_pared, 4, 4),
            "fisica_velocidad": FuncionNativa("fisica_velocidad", self._nativa_fisica_velocidad, 3, 3),
            "fisica_fuerza": FuncionNativa("fisica_fuerza", self._nativa_fisica_fuerza, 3, 3),
            "fisica_rebote": FuncionNativa("fisica_rebote", self._nativa_fisica_rebote, 2, 2),
            "fisica_friccion": FuncionNativa("fisica_friccion", self._nativa_fisica_friccion, 2, 2),
            "fisica_en_suelo": FuncionNativa("fisica_en_suelo", self._nativa_fisica_en_suelo, 1, 1),
            "colision_hay": FuncionNativa("colision_hay", self._nativa_colision_hay, 2, 2),
            "colision_al_chocar": FuncionNativa("colision_al_chocar", self._nativa_colision_al_chocar, 2, 3),
            # Sprites avanzados, audio, mapas y cámara (Avadia 1.2)
            "sprite_transparencia": FuncionNativa("sprite_transparencia", self._nativa_sprite_transparencia, 2, 2),
            "sonido_reproducir": FuncionNativa("sonido_reproducir", self._nativa_sonido_reproducir, 1, 1),
            "musica_reproducir": FuncionNativa("musica_reproducir", self._nativa_musica_reproducir, 1, 1),
            "musica_pausar": FuncionNativa("musica_pausar", self._nativa_musica_pausar, 0, 0),
            "musica_reanudar": FuncionNativa("musica_reanudar", self._nativa_musica_reanudar, 0, 0),
            "musica_detener": FuncionNativa("musica_detener", self._nativa_musica_detener, 0, 0),
            "musica_volumen": FuncionNativa("musica_volumen", self._nativa_musica_volumen, 1, 1),
            "mapa_crear": FuncionNativa("mapa_crear", self._nativa_mapa_crear, 3, 3),
            "mapa_cargar": FuncionNativa("mapa_cargar", self._nativa_mapa_cargar, 1, 1),
            "mapa_guardar": FuncionNativa("mapa_guardar", self._nativa_mapa_guardar, 1, 1),
            "mapa_tileset": FuncionNativa("mapa_tileset", self._nativa_mapa_tileset, 3, 3),
            "mapa_bloque": FuncionNativa("mapa_bloque", self._nativa_mapa_bloque, 4, 4),
            "mapa_obtener": FuncionNativa("mapa_obtener", self._nativa_mapa_obtener, 3, 3),
            "mapa_solido": FuncionNativa("mapa_solido", self._nativa_mapa_solido, 1, 1),
            "mapa_colisiones": FuncionNativa("mapa_colisiones", self._nativa_mapa_colisiones, 0, 0),
            "camara_seguir": FuncionNativa("camara_seguir", self._nativa_camara_seguir, 1, 1),
            "camara_mover": FuncionNativa("camara_mover", self._nativa_camara_mover, 2, 2),
            "camara_posicion": FuncionNativa("camara_posicion", self._nativa_camara_posicion, 0, 0),
            "json_leer": FuncionNativa("json_leer", self._nativa_json_leer, 1, 1),
            "json_escribir": FuncionNativa("json_escribir", self._nativa_json_escribir, 2, 2),
        }
        for nombre, funcion in funciones.items():
            registrada = self.registro.agregar(nombre, funcion.funcion, funcion.minimo, funcion.maximo)
            self.entorno.definir(nombre, registrada)

    def cargar_biblioteca(self, nombre, registrar):
        """Registra una biblioteca externa sin modificar el núcleo del intérprete.

        `registrar(registro)` debe llamar a registro.agregar(...) para cada función.
        """
        if not isinstance(nombre, str) or not nombre.isidentifier():
            raise ErrorEjecucion(f"Nombre de biblioteca no válido: {nombre!r}")
        if nombre in self.bibliotecas_cargadas:
            raise ErrorEjecucion(f"La biblioteca '{nombre}' ya está cargada")
        antes = set(self.registro.funciones)
        try:
            registrar(self.registro)
        except ErrorRegistro as error:
            raise ErrorEjecucion(f"No se pudo cargar la biblioteca '{nombre}': {error}") from None
        for funcion in sorted(set(self.registro.funciones) - antes):
            self.entorno.definir(funcion, self.registro.funciones[funcion])
        self.bibliotecas_cargadas.add(nombre)
        return True

    def ejecutar(self, programa, archivo_actual=None):
        anterior = self.archivo_actual
        if archivo_actual is not None:
            self.archivo_actual = Path(archivo_actual).resolve()
        try:
            try:
                self._ejecutar_nodo(programa)
            except _RetornoFuncion:
                raise ErrorEjecucion("'retornar' solo puede utilizarse dentro de una función") from None
            except _RomperBucle:
                raise ErrorEjecucion("'romper' solo puede utilizarse dentro de un ciclo") from None
        finally:
            self.archivo_actual = anterior

    def _ejecutar_nodo(self, nodo):
        try:
            if self.depurador is not None:
                self.depurador.antes(nodo, self)
            return self._ejecutar_nodo_base(nodo)
        except ErrorEjecucion as error:
            if error.linea is None and hasattr(nodo, "linea"):
                error.linea = nodo.linea
                error.columna = getattr(nodo, "columna", None)
            if error.archivo is None and self.archivo_actual is not None:
                error.archivo = self.archivo_actual
            raise

    def _ejecutar_nodo_base(self, nodo):
        if isinstance(nodo, Programa):
            for instruccion in nodo.instrucciones:
                self._ejecutar_nodo(instruccion)
        elif isinstance(nodo, CrearVariable):
            valor = self._evaluar(nodo.valor)
            if not cumple(valor, nodo.tipo):
                raise ErrorEjecucion(f"La variable '{nodo.nombre}' es de tipo {nodo.tipo}, pero se le asignó {nombre_de_valor(valor)}",
                                     sugerencia=f"Usa un valor de tipo {nodo.tipo} o quita la anotación de tipo")
            self.entorno.definir(nodo.nombre, valor, nodo.tipo)
        elif isinstance(nodo, AsignarVariable):
            valor = self._evaluar(nodo.valor)
            self.entorno.asignar(nodo.nombre, valor)
        elif isinstance(nodo, AsignarIndice):
            objeto = self._evaluar(nodo.objeto)
            indice = self._evaluar(nodo.indice)
            valor = self._evaluar(nodo.valor)
            if isinstance(objeto, dict):
                self._validar_clave(indice)
                objeto[indice] = valor
            elif isinstance(objeto, list):
                if not isinstance(indice, int) or isinstance(indice, bool):
                    raise ErrorEjecucion("El índice de una lista debe ser un número entero")
                if not -len(objeto) <= indice < len(objeto):
                    raise ErrorEjecucion(f"El índice {indice} está fuera de los límites (longitud {len(objeto)})",
                                         sugerencia="Usa agregar(lista, valor) para añadir al final")
                objeto[indice] = valor
            else:
                raise ErrorEjecucion("Solo se puede asignar a elementos de listas y diccionarios")
        elif isinstance(nodo, Mostrar):
            self.salida(self._formatear(self._evaluar(nodo.expresion)))
        elif isinstance(nodo, ExpresionSentencia):
            self._evaluar(nodo.expresion)
        elif isinstance(nodo, Condicional):
            rama = nodo.entonces if self._verdadero(self._evaluar(nodo.condicion)) else nodo.sino
            for instruccion in rama:
                self._ejecutar_nodo(instruccion)
        elif isinstance(nodo, Mientras):
            vueltas = 0
            while self._verdadero(self._evaluar(nodo.condicion)):
                vueltas += 1
                if vueltas > self.MAX_ITERACIONES:
                    raise ErrorEjecucion("El ciclo superó el límite de seguridad de iteraciones")
                try:
                    for instruccion in nodo.cuerpo:
                        self._ejecutar_nodo(instruccion)
                except _RomperBucle:
                    break
        elif isinstance(nodo, Para):
            iterable = self._evaluar(nodo.iterable)
            if isinstance(iterable, dict):
                iterable = list(iterable.keys())
            if not isinstance(iterable, (list, tuple, str, range)):
                raise ErrorEjecucion("'para' necesita una lista, un diccionario, un texto o un rango")
            self.entorno.definir(nodo.nombre, None)
            vueltas = 0
            for elemento in iterable:
                vueltas += 1
                if vueltas > self.MAX_ITERACIONES:
                    raise ErrorEjecucion("El ciclo superó el límite de seguridad de iteraciones")
                self.entorno.asignar(nodo.nombre, elemento)
                try:
                    for instruccion in nodo.cuerpo:
                        self._ejecutar_nodo(instruccion)
                except _RomperBucle:
                    break
        elif isinstance(nodo, Funcion):
            self.entorno.definir(nodo.nombre, FuncionAvadia(nodo, self.entorno))
        elif isinstance(nodo, Retornar):
            raise _RetornoFuncion(None if nodo.expresion is None else self._evaluar(nodo.expresion))
        elif isinstance(nodo, Romper):
            raise _RomperBucle()
        elif isinstance(nodo, Importar):
            self._importar(nodo)
        elif isinstance(nodo, Ayuda):
            self._mostrar_ayuda()
        else:
            raise ErrorEjecucion(f"No se puede ejecutar el nodo {type(nodo).__name__}")

    def _evaluar(self, nodo):
        if isinstance(nodo, Literal):
            return nodo.valor
        if isinstance(nodo, Variable):
            return self.entorno.obtener(nodo.nombre)
        if isinstance(nodo, ListaLiteral):
            return [self._evaluar(x) for x in nodo.elementos]
        if isinstance(nodo, DiccionarioLiteral):
            diccionario = {}
            for clave_nodo, valor_nodo in nodo.pares:
                clave = self._evaluar(clave_nodo)
                self._validar_clave(clave)
                diccionario[clave] = self._evaluar(valor_nodo)
            return diccionario
        if isinstance(nodo, AccesoIndice):
            objeto = self._evaluar(nodo.objeto)
            indice = self._evaluar(nodo.indice)
            if isinstance(objeto, dict):
                self._validar_clave(indice)
                if indice not in objeto:
                    raise ErrorEjecucion(f"La clave {indice!r} no existe en el diccionario",
                                         sugerencia="Comprueba la clave con 'en' antes de leerla, o créala asignando un valor")
                return objeto[indice]
            if not isinstance(indice, int) or isinstance(indice, bool):
                raise ErrorEjecucion("El índice de una lista debe ser un número entero")
            if not isinstance(objeto, (list, str)):
                raise ErrorEjecucion("Solo se puede usar [ ] con listas, textos y diccionarios")
            try:
                return objeto[indice]
            except IndexError:
                raise ErrorEjecucion(f"El índice {indice} está fuera de los límites (longitud {len(objeto)})",
                                     sugerencia="Los índices empiezan en 0 y llegan hasta longitud - 1") from None
        if isinstance(nodo, OperacionUnaria):
            valor = self._evaluar(nodo.operando)
            try:
                if nodo.operador == "-": return -valor
                if nodo.operador == "+": return +valor
                if nodo.operador == "no": return not self._verdadero(valor)
            except TypeError:
                raise ErrorEjecucion(f"El operador '{nodo.operador}' no acepta ese tipo de valor") from None
        if isinstance(nodo, OperacionBinaria):
            return self._evaluar_binaria(nodo)
        if isinstance(nodo, Llamada):
            funcion = self._evaluar(nodo.funcion)
            argumentos = [self._evaluar(x) for x in nodo.argumentos]
            return self._llamar(funcion, argumentos)
        raise ErrorEjecucion(f"No se puede evaluar el nodo {type(nodo).__name__}")

    def _evaluar_binaria(self, nodo):
        izquierda = self._evaluar(nodo.izquierda)
        if nodo.operador == "y":
            return self._verdadero(izquierda) and self._verdadero(self._evaluar(nodo.derecha))
        if nodo.operador == "o":
            return self._verdadero(izquierda) or self._verdadero(self._evaluar(nodo.derecha))
        derecha = self._evaluar(nodo.derecha)
        operaciones = {
            "+": lambda: izquierda + derecha,
            "-": lambda: izquierda - derecha,
            "*": lambda: izquierda * derecha,
            "/": lambda: izquierda / derecha,
            "%": lambda: izquierda % derecha,
            "==": lambda: izquierda == derecha,
            "!=": lambda: izquierda != derecha,
            "<": lambda: izquierda < derecha,
            ">": lambda: izquierda > derecha,
            "<=": lambda: izquierda <= derecha,
            ">=": lambda: izquierda >= derecha,
            "en": lambda: izquierda in derecha,
        }
        try:
            if nodo.operador == "/" and derecha == 0:
                raise ErrorEjecucion("No se puede dividir entre cero", sugerencia="Revisa el divisor antes de dividir")
            if nodo.operador == "%" and derecha == 0:
                raise ErrorEjecucion("No se puede calcular el módulo entre cero")
            if nodo.operador not in operaciones:
                raise ErrorEjecucion(f"Operador desconocido: {nodo.operador}")
            return operaciones[nodo.operador]()
        except ErrorEjecucion:
            raise
        except (TypeError, ValueError) as error:
            raise ErrorEjecucion(f"Operación '{nodo.operador}' no válida: {error}") from None

    def _llamar(self, funcion, argumentos):
        if isinstance(funcion, FuncionNativa):
            if not funcion.minimo <= len(argumentos) <= funcion.maximo:
                rango = str(funcion.minimo) if funcion.minimo == funcion.maximo else f"{funcion.minimo} a {funcion.maximo}"
                raise ErrorEjecucion(f"'{funcion.nombre}' necesita {rango} argumento(s); recibió {len(argumentos)}")
            try:
                return funcion.funcion(*argumentos)
            except ErrorEjecucion:
                raise
            except (TypeError, ValueError, OverflowError) as error:
                raise ErrorEjecucion(f"Error en '{funcion.nombre}': {error}") from None
        if isinstance(funcion, FuncionAvadia):
            declaracion = funcion.declaracion
            if len(argumentos) != len(declaracion.parametros):
                raise ErrorEjecucion(f"La función '{declaracion.nombre}' necesita {len(declaracion.parametros)} argumento(s)")
            anterior = self.entorno
            local = Entorno(funcion.cierre)
            for nombre, valor in zip(declaracion.parametros, argumentos):
                local.definir(nombre, valor)
            self.entorno = local
            self.pila_llamadas.append(declaracion.nombre)
            try:
                for instruccion in declaracion.cuerpo:
                    self._ejecutar_nodo(instruccion)
            except _RetornoFuncion as retorno:
                return retorno.valor
            finally:
                self.entorno = anterior
                self.pila_llamadas.pop()
            return None
        raise ErrorEjecucion("El valor indicado no se puede utilizar como función")

    def _nativa_leer(self, mensaje=""):
        try:
            return self.entrada(str(mensaje))
        except EOFError:
            raise ErrorEjecucion("No se recibió ningún dato de entrada") from None

    @staticmethod
    def _nativa_longitud(valor):
        return len(valor)

    @staticmethod
    def _nativa_agregar(lista, valor):
        if not isinstance(lista, list):
            raise ErrorEjecucion("agregar necesita una lista como primer argumento")
        lista.append(valor)
        return lista

    def _nativa_quitar(self, lista, indice=None):
        if isinstance(lista, dict):
            if indice is None:
                raise ErrorEjecucion("quitar necesita la clave a eliminar en un diccionario")
            if indice not in lista:
                raise ErrorEjecucion(f"La clave {indice!r} no existe en el diccionario")
            return lista.pop(indice)
        if not isinstance(lista, list):
            raise ErrorEjecucion("quitar necesita una lista o un diccionario como primer argumento")
        if indice is None:
            indice = -1
        if not isinstance(indice, int):
            raise ErrorEjecucion("El índice de quitar debe ser entero")
        try:
            return lista.pop(indice)
        except IndexError:
            raise ErrorEjecucion("Índice fuera de los límites de la lista") from None

    @staticmethod
    def _nativa_rango(inicio, fin=None, paso=1):
        if fin is None:
            inicio, fin = 0, inicio
        if not all(isinstance(x, int) for x in (inicio, fin, paso)):
            raise ErrorEjecucion("rango solo acepta números enteros")
        if paso == 0:
            raise ErrorEjecucion("El paso de rango no puede ser cero")
        return range(inicio, fin, paso)

    @staticmethod
    def _nativa_texto(valor):
        if isinstance(valor, bool): return "verdadero" if valor else "falso"
        if valor is None: return "nulo"
        return str(valor)

    @staticmethod
    def _nativa_numero(valor):
        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            return valor
        texto = str(valor).strip()
        try:
            return float(texto) if "." in texto else int(texto)
        except ValueError:
            raise ErrorEjecucion(f"No se puede convertir {valor!r} en número") from None

    @staticmethod
    def _nativa_tipo(valor):
        if isinstance(valor, bool): return "booleano"
        if isinstance(valor, int): return "entero"
        if isinstance(valor, float): return "decimal"
        if isinstance(valor, str): return "texto"
        if isinstance(valor, list): return "lista"
        if isinstance(valor, dict): return "diccionario"
        if valor is None: return "nulo"
        if isinstance(valor, (FuncionAvadia, FuncionNativa)): return "funcion"
        return "desconocido"

    # ------------------------------------------------------------
    # Biblioteca 2D: las funciones de Avadia llaman a Motor2D.
    # ------------------------------------------------------------
    def _nativa_juego_ventana(self, ancho=800, alto=600, titulo="Juego creado con Avadia"):
        try:
            return self.juego2d.configurar_ventana(ancho, alto, titulo)
        except ErrorJuego2D as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_juego_limpiar(self, color="#20242b"):
        try:
            return self.juego2d.limpiar(color)
        except ErrorJuego2D as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_juego_rectangulo(self, x, y, ancho, alto, color="#e74c3c"):
        try:
            return self.juego2d.rectangulo(x, y, ancho, alto, color)
        except ErrorJuego2D as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_juego_circulo(self, x, y, diametro, color="#3498db"):
        try:
            return self.juego2d.circulo(x, y, diametro, color)
        except ErrorJuego2D as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_juego_texto(self, x, y, contenido, color="#ffffff", tamano=20):
        try:
            return self.juego2d.texto(x, y, contenido, color, tamano)
        except ErrorJuego2D as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_juego_tecla(self, nombre):
        return self.juego2d.tecla_presionada(nombre)

    def _nativa_juego_iniciar(self, actualizar):
        if not isinstance(actualizar, FuncionAvadia):
            raise ErrorEjecucion("juego_iniciar necesita el nombre de una función Avadia")
        try:
            return self.juego2d.iniciar(lambda: self._llamar(actualizar, []))
        except ErrorJuego2D as error:
            raise ErrorEjecucion(str(error)) from None

    # ------------------------------------------------------------
    # Biblioteca web: genera HTML/CSS y puede servirlo en localhost.
    # ------------------------------------------------------------
    def _nativa_web_iniciar(self, titulo="Mi página Avadia"):
        return self.creador_web.iniciar(titulo)

    def _nativa_web_titulo(self, texto):
        return self.creador_web.agregar_titulo(texto)

    def _nativa_web_parrafo(self, texto):
        return self.creador_web.agregar_parrafo(texto)

    def _nativa_web_boton(self, texto, enlace="#"):
        try:
            return self.creador_web.agregar_boton(texto, enlace)
        except ErrorWeb as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_web_imagen(self, ruta, descripcion=""):
        return self.creador_web.agregar_imagen(ruta, descripcion)

    def _nativa_web_estilo(self, css):
        return self.creador_web.establecer_estilo(css)

    def _nativa_web_html(self, codigo):
        return self.creador_web.agregar_html(codigo)

    def _web(self, funcion, *argumentos):
        try:
            return getattr(self.creador_web, funcion)(*argumentos)
        except ErrorWeb as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_web_formulario_iniciar(self, nombre):
        return self._web("formulario_iniciar", nombre)

    def _nativa_web_campo(self, nombre, etiqueta, tipo="texto", requerido=False, minimo=None):
        return self._web("agregar_campo", nombre, etiqueta, tipo, requerido, minimo)

    def _nativa_web_casilla(self, nombre, etiqueta, requerido=False):
        return self._web("agregar_casilla", nombre, etiqueta, requerido)

    def _nativa_web_formulario_enviar(self, texto="Enviar"):
        return self._web("enviar_formulario", texto)

    def _nativa_web_bloque_iniciar(self, id_bloque, diseno="bloque"):
        return self._web("bloque_iniciar", id_bloque, diseno)

    def _nativa_web_componente(self, nombre, plantilla):
        return self._web("componente_definir", nombre, plantilla)

    def _nativa_web_usar(self, nombre, valores):
        return self._web("componente_usar", nombre, valores)

    def _nativa_web_menu(self, elementos):
        return self._web("agregar_menu", elementos)

    def _nativa_web_tarjeta(self, titulo, texto, imagen=""):
        return self._web("agregar_tarjeta", titulo, texto, imagen)

    def _indice_recursos(self):
        from herramientas.proyectos import indexar_recursos, ErrorProyecto
        base = self.archivo_actual.parent if self.archivo_actual else Path.cwd()
        try:
            return indexar_recursos(base)
        except ErrorProyecto as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_recurso(self, nombre):
        indice = self._indice_recursos()
        if nombre not in indice:
            raise ErrorEjecucion(f"No existe el recurso '{nombre}'",
                                 sugerencia="Coloca el archivo en la carpeta recursos/ del proyecto (sin contar la extensión)")
        return indice[nombre]

    def _nativa_recursos(self):
        return sorted(self._indice_recursos().keys())

    def _nativa_web_bloque_cerrar(self):
        return self._web("bloque_cerrar")

    def _nativa_web_boton_accion(self, texto, id_bloque, accion):
        return self._web("agregar_boton_accion", texto, id_bloque, accion)

    def _nativa_web_guardar(self, ruta):
        base = self.archivo_actual.parent if self.archivo_actual else Path.cwd()
        try:
            resultado = self.creador_web.guardar(ruta, carpeta_base=base)
            self.salida(f"Página web guardada en: {resultado}")
            return resultado
        except (OSError, ErrorWeb) as error:
            raise ErrorEjecucion(f"No se pudo guardar la página: {error}") from None

    def _nativa_web_servidor(self, puerto=8000):
        try:
            return self.creador_web.servidor(puerto)
        except ErrorWeb as error:
            raise ErrorEjecucion(str(error)) from None

    @staticmethod
    def _validar_clave(clave):
        if not isinstance(clave, (str, int, float, bool)):
            raise ErrorEjecucion("Una clave de diccionario debe ser texto, número o booleano")

    # ------------------------------------------------------------
    # Biblioteca de archivos: siempre dentro de la carpeta del proyecto.
    # ------------------------------------------------------------
    def _biblioteca_archivos(self):
        base = self.archivo_actual.parent if self.archivo_actual else Path.cwd()
        return BibliotecaArchivos(base)

    def _ejecutar_archivo(self, operacion, *argumentos):
        try:
            return getattr(self._biblioteca_archivos(), operacion)(*argumentos)
        except ErrorArchivo as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_archivo_leer(self, ruta):
        return self._ejecutar_archivo("archivo_leer", ruta)

    def _nativa_archivo_escribir(self, ruta, contenido):
        return self._ejecutar_archivo("archivo_escribir", ruta, contenido)

    def _nativa_archivo_agregar(self, ruta, contenido):
        return self._ejecutar_archivo("archivo_agregar", ruta, contenido)

    def _nativa_archivo_existe(self, ruta):
        return self._ejecutar_archivo("archivo_existe", ruta)

    def _nativa_carpeta_crear(self, ruta):
        return self._ejecutar_archivo("carpeta_crear", ruta)

    def _nativa_archivo_listar(self, ruta="."):
        return self._ejecutar_archivo("archivo_listar", ruta)

    def _nativa_archivo_eliminar(self, ruta, confirmar):
        return self._ejecutar_archivo("archivo_eliminar", ruta, confirmar)

    # ------------------------------------------------------------
    # Sprites y animaciones: las rutas de imagen también quedan en el proyecto.
    # ------------------------------------------------------------
    def _ruta_imagen(self, ruta):
        try:
            return str(self._biblioteca_archivos().resolver(ruta))
        except ErrorArchivo as error:
            raise ErrorEjecucion(str(error)) from None

    def _sprite(self, funcion, *argumentos):
        try:
            return getattr(self.juego2d.sprites, funcion)(*argumentos)
        except ErrorSprite as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_sprite_cargar(self, ruta, x=0, y=0):
        return self._sprite("cargar", self._ruta_imagen(ruta), x, y)

    def _nativa_sprite_hoja(self, ruta, ancho_cuadro, alto_cuadro, x=0, y=0):
        return self._sprite("cargar", self._ruta_imagen(ruta), x, y, ancho_cuadro, alto_cuadro)

    def _nativa_sprite_mover(self, id_sprite, x, y):
        resultado = self._sprite("mover", id_sprite, x, y)
        cuerpo = self.juego2d.fisica.cuerpos.get(id_sprite)
        if cuerpo is not None and not cuerpo.estatico:
            cuerpo.x, cuerpo.y = float(x), float(y)
        return resultado

    def _nativa_sprite_posicion(self, id_sprite):
        return self._sprite("posicion", id_sprite)

    def _nativa_sprite_escala(self, id_sprite, escala):
        return self._sprite("escalar", id_sprite, escala)

    def _nativa_sprite_rotar(self, id_sprite, grados):
        return self._sprite("rotar", id_sprite, grados)

    def _nativa_sprite_capa(self, id_sprite, capa):
        return self._sprite("capa", id_sprite, capa)

    def _nativa_sprite_eliminar(self, id_sprite):
        resultado = self._sprite("eliminar", id_sprite)
        self.juego2d.fisica.quitar(id_sprite)
        return resultado

    def _nativa_animacion_crear(self, id_sprite, nombre, cuadros, fps=8):
        return self._sprite("animacion_crear", id_sprite, nombre, cuadros, fps)

    def _nativa_animacion_reproducir(self, id_sprite, nombre):
        return self._sprite("animacion_reproducir", id_sprite, nombre)

    def _nativa_animacion_pausar(self, id_sprite):
        return self._sprite("animacion_pausar", id_sprite)

    def _nativa_animacion_detener(self, id_sprite):
        return self._sprite("animacion_detener", id_sprite)

    def _nativa_animacion_velocidad(self, id_sprite, fps):
        return self._sprite("animacion_velocidad", id_sprite, fps)

    # ------------------------------------------------------------
    # Física y colisiones
    # ------------------------------------------------------------
    def _fisica(self, funcion, *argumentos):
        try:
            return getattr(self.juego2d.fisica, funcion)(*argumentos)
        except ErrorFisica as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_fisica_gravedad(self, valor):
        if not isinstance(valor, (int, float)) or isinstance(valor, bool):
            raise ErrorEjecucion("La gravedad debe ser un número")
        self.juego2d.fisica.gravedad = float(valor)
        return True

    def _nativa_fisica_activar(self, id_sprite, ancho, alto, masa=1, forma="rectangulo"):
        x, y = self._sprite("posicion", id_sprite)
        return self._fisica("activar", id_sprite, x, y, ancho, alto, forma, masa)

    def _nativa_fisica_pared(self, x, y, ancho, alto):
        return self._fisica("pared", x, y, ancho, alto)

    def _nativa_fisica_velocidad(self, id_cuerpo, vx, vy):
        return self._fisica("velocidad", id_cuerpo, vx, vy)

    def _nativa_fisica_fuerza(self, id_cuerpo, fx, fy):
        return self._fisica("fuerza", id_cuerpo, fx, fy)

    def _nativa_fisica_rebote(self, id_cuerpo, valor):
        return self._fisica("configurar", id_cuerpo, rebote=valor)

    def _nativa_fisica_friccion(self, id_cuerpo, valor):
        return self._fisica("configurar", id_cuerpo, friccion=valor)

    def _nativa_fisica_en_suelo(self, id_cuerpo):
        return self._fisica("en_suelo", id_cuerpo)

    def _nativa_colision_hay(self, a, b):
        return self._fisica("hay_colision", a, b)

    def _nativa_colision_al_chocar(self, a, b, funcion=None):
        if funcion is None:
            # Forma corta: colision_al_chocar(sprite, funcion) detecta cualquier choque.
            funcion, b = b, None
        if not isinstance(funcion, FuncionAvadia):
            raise ErrorEjecucion("colision_al_chocar necesita el nombre de una función Avadia")
        return self._fisica("suscribir", a, b, funcion)

    def _despachar_colision(self, funcion, a, b):
        self._llamar(funcion, [a, b])

    # ------------------------------------------------------------
    # Sprites avanzados, audio, mapas y cámara
    # ------------------------------------------------------------
    def _nativa_sprite_transparencia(self, id_sprite, opacidad):
        return self._sprite("transparencia", id_sprite, opacidad)

    def _audio(self, funcion, *argumentos):
        try:
            return getattr(self.juego2d.audio, funcion)(*argumentos)
        except ErrorAudio as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_sonido_reproducir(self, ruta):
        return self._audio("sonido", self._ruta_imagen(ruta))

    def _nativa_musica_reproducir(self, ruta):
        return self._audio("musica", self._ruta_imagen(ruta))

    def _nativa_musica_pausar(self):
        return self._audio("pausar")

    def _nativa_musica_reanudar(self):
        return self._audio("reanudar")

    def _nativa_musica_detener(self):
        return self._audio("detener")

    def _nativa_musica_volumen(self, valor):
        return self._audio("volumen", valor)

    def _mapa(self):
        if self.juego2d.mapa is None:
            raise ErrorEjecucion("No hay ningún mapa activo",
                                 sugerencia="Crea uno con mapa_crear o carga uno con mapa_cargar")
        return self.juego2d.mapa

    def _mapa_op(self, funcion, *argumentos):
        try:
            return getattr(self._mapa(), funcion)(*argumentos)
        except ErrorMapa as error:
            raise ErrorEjecucion(str(error)) from None

    def _nativa_mapa_crear(self, ancho, alto, tam):
        try:
            self.juego2d.mapa = Mapa(ancho, alto, tam)
        except ErrorMapa as error:
            raise ErrorEjecucion(str(error)) from None
        self.juego2d.actualizar_paredes_mapa()
        return True

    def _nativa_mapa_cargar(self, ruta):
        try:
            mapa = Mapa.desde_archivo(self._ruta_imagen(ruta))
        except ErrorMapa as error:
            raise ErrorEjecucion(str(error)) from None
        if mapa.tileset:
            mapa.tileset = self._ruta_imagen(mapa.tileset)
        self.juego2d.mapa = mapa
        self.juego2d.actualizar_paredes_mapa()
        return True

    def _nativa_mapa_guardar(self, ruta):
        destino = self._ruta_imagen(ruta)
        try:
            self._mapa().guardar(destino)
        except OSError as error:
            raise ErrorEjecucion(f"No se pudo guardar el mapa: {error}") from None
        return destino

    def _nativa_mapa_tileset(self, ruta, ancho_tile, alto_tile):
        mapa = self._mapa()
        if not all(isinstance(v, int) and v > 0 for v in (ancho_tile, alto_tile)):
            raise ErrorEjecucion("El tamaño de cada mosaico debe ser un entero positivo")
        mapa.tileset = self._ruta_imagen(ruta)
        mapa.tile_ancho, mapa.tile_alto = ancho_tile, alto_tile
        mapa._cache_tiles.clear()
        mapa._hoja = None
        return True

    def _nativa_mapa_bloque(self, capa, x, y, id_mosaico):
        resultado = self._mapa_op("poner", capa, x, y, id_mosaico)
        self.juego2d.actualizar_paredes_mapa()
        return resultado

    def _nativa_mapa_obtener(self, capa, x, y):
        return self._mapa_op("obtener", capa, x, y)

    def _nativa_mapa_solido(self, id_mosaico):
        resultado = self._mapa_op("solido", id_mosaico)
        self.juego2d.actualizar_paredes_mapa()
        return resultado

    def _nativa_mapa_colisiones(self):
        self.juego2d.actualizar_paredes_mapa()
        return len(self.juego2d.paredes_mapa)

    def _nativa_camara_seguir(self, id_sprite):
        self._sprite("posicion", id_sprite)  # valida que el sprite exista
        return self.juego2d.camara.seguir(id_sprite)

    def _nativa_camara_mover(self, x, y):
        return self.juego2d.camara.mover(x, y)

    def _nativa_camara_posicion(self):
        return [self.juego2d.camara.x, self.juego2d.camara.y]

    def _nativa_json_leer(self, ruta):
        return self._ejecutar_archivo("json_leer", ruta)

    def _nativa_json_escribir(self, ruta, valor):
        return self._ejecutar_archivo("json_escribir", ruta, valor)

    @staticmethod
    def _verdadero(valor):
        return bool(valor)

    def _formatear(self, valor):
        if valor is True: return "verdadero"
        if valor is False: return "falso"
        if valor is None: return "nulo"
        if isinstance(valor, list):
            return "[" + ", ".join(self._formatear(x) for x in valor) + "]"
        if isinstance(valor, range):
            return "[" + ", ".join(str(x) for x in valor) + "]"
        if isinstance(valor, dict):
            return "{" + ", ".join(f"{self._formatear(k)}: {self._formatear(v)}" for k, v in valor.items()) + "}"
        return str(valor)

    def _importar(self, nodo):
        ruta_valor = self._evaluar(nodo.ruta)
        if not isinstance(ruta_valor, str):
            raise ErrorEjecucion("importar necesita la ruta de un archivo entre comillas")
        base = self.archivo_actual.parent if self.archivo_actual else Path.cwd()
        ruta = (base / ruta_valor).resolve()
        if ruta in self.pila_importaciones:
            raise ErrorEjecucion(f"Se detectó una importación circular: {ruta.name}")
        if ruta in self.rutas_importadas:
            return
        if not ruta.is_file():
            raise ErrorEjecucion(f"No se encontró el módulo '{ruta_valor}'")
        self.pila_importaciones.append(ruta)
        anterior = self.archivo_actual
        self.archivo_actual = ruta
        try:
            codigo = ruta.read_text(encoding="utf-8")
            arbol = Parser(Lexer(codigo).tokenizar()).analizar()
            self._ejecutar_nodo(arbol)
            self.rutas_importadas.add(ruta)
        except (OSError, ErrorLexico, ErrorSintactico) as error:
            raise ErrorEjecucion(f"No se pudo importar '{ruta_valor}': {error}") from None
        finally:
            self.archivo_actual = anterior
            self.pila_importaciones.pop()

    def _mostrar_ayuda(self):
        lineas = [
            "AVADIA 1.3 — Ayuda rápida",
            "crear nombre = expresión     Crear una variable",
            "nombre = expresión           Modificar una variable existente",
            "mostrar expresión            Mostrar un valor",
            "si condición entonces ... fin   Condicional (admite sino)",
            "mientras condición hacer ... fin   Ciclo condicional",
            "para elemento en lista hacer ... fin   Recorrido",
            "funcion nombre(a, b) ... fin   Declarar una función",
            "retornar expresión           Devolver un resultado",
            "romper                       Salir del ciclo actual",
            'importar "archivo.av"        Cargar otro archivo Avadia',
            "leer, longitud, agregar, quitar, rango, texto, numero, tipo",
            "Diccionarios: d = {\"clave\": valor}, d[\"clave\"] = nuevo, quitar(d, \"clave\")",
            "Listas anidadas: m[0][1] = valor",
            "Sprites: sprite_cargar, sprite_hoja, sprite_mover, sprite_posicion, sprite_escala, sprite_rotar, sprite_capa, sprite_eliminar",
            "Animaciones: animacion_crear, animacion_reproducir, animacion_pausar, animacion_detener, animacion_velocidad",
            "Física: fisica_gravedad, fisica_activar, fisica_pared, fisica_velocidad, fisica_fuerza, fisica_rebote, fisica_friccion, fisica_en_suelo",
            "Colisiones: colision_hay, colision_al_chocar(a, [b], función) — la función recibe los dos ids",
            "Web formularios: web_formulario_iniciar, web_campo, web_casilla, web_formulario_enviar; bloques: web_bloque_iniciar, web_bloque_cerrar, web_boton_accion",
            "Componentes web: web_componente(nombre, html con {marcas}), web_usar(nombre, {marca: valor}), web_menu([[texto, enlace]]), web_tarjeta(título, texto, [imagen])",
            "Tipos opcionales: crear edad: entero = 20  (tipos: entero, decimal, numero, texto, booleano, lista, diccionario, cualquiera)",
            "Recursos: recurso(nombre) devuelve la ruta de un archivo de recursos/; recursos() lista los nombres",
            "Audio (WAV en Windows): sonido_reproducir, musica_reproducir, musica_pausar, musica_reanudar, musica_detener",
            "Mapas: mapa_crear, mapa_cargar, mapa_guardar, mapa_tileset, mapa_bloque, mapa_obtener, mapa_solido, mapa_colisiones",
            "Cámara y sprites: camara_seguir, camara_mover, camara_posicion, sprite_transparencia",
            "Archivos: archivo_leer, archivo_escribir, archivo_agregar, archivo_existe, carpeta_crear, archivo_listar, archivo_eliminar(ruta, \"si\"), json_leer, json_escribir",
            "2D: juego_ventana, juego_iniciar, juego_limpiar, juego_rectangulo, juego_circulo, juego_texto, juego_tecla",
            "Web: web_iniciar, web_titulo, web_parrafo, web_boton, web_imagen, web_estilo, web_guardar, web_servidor",
            "web_html inserta HTML sin filtrar: úsalo solo con contenido escrito por ti y de confianza",
            "Operadores: + - * / %, == != < > <= >=, y, o, no, en",
            "Los comentarios comienzan con //",
        ]
        for linea in lineas:
            self.salida(linea)
