"""Consola de Avadia 1.2 (Creator)."""
import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path

from lexer import Lexer
from parser import Parser
from interprete import Interprete
from nucleo.errores import AvadiaError
from nucleo.semantica import analizar_semantica

VERSION = "1.3.0"


def a_datos(objeto):
    if is_dataclass(objeto):
        datos = asdict(objeto)
        return {"nodo": type(objeto).__name__, **{k: a_datos(v) for k, v in datos.items()}}
    if isinstance(objeto, list):
        return [a_datos(x) for x in objeto]
    return objeto


def imprimir_diagnostico(titulo, mensaje, archivo, linea=None, columna=None, sugerencia=None):
    """Formato único para errores y advertencias de Avadia."""
    print(titulo)
    print(f"Archivo: {archivo}")
    if linea is not None:
        print(f"Línea: {linea}")
    if columna is not None:
        print(f"Columna: {columna}")
    print(f"Problema: {mensaje}")
    if sugerencia:
        print(f"Sugerencia: {sugerencia}")


def imprimir_error(error, ruta_principal):
    imprimir_diagnostico(f"ERROR DE {error.tipo}", error.mensaje, error.archivo or ruta_principal,
                         error.linea, error.columna, error.sugerencia)


def verificar(arbol, ruta, informar_si_todo_bien=False):
    """Muestra advertencias y errores semánticos. Devuelve True si el programa puede ejecutarse."""
    resultado = analizar_semantica(arbol)
    for aviso in resultado.advertencias:
        imprimir_diagnostico("ADVERTENCIA", aviso.mensaje, ruta, aviso.linea, aviso.columna, aviso.sugerencia)
    for error in resultado.errores:
        imprimir_error(type("E", (), {"tipo": error.tipo, "mensaje": error.mensaje, "archivo": None,
                                      "linea": error.linea, "columna": error.columna,
                                      "sugerencia": error.sugerencia})(), ruta)
    if informar_si_todo_bien and not resultado.advertencias and not resultado.errores:
        print("Sin errores ni advertencias.")
    return resultado.correcto


def _crear_parser():
    analizador = argparse.ArgumentParser(
        prog="avadia",
        description="Avadia 1.2 Creator — lenguaje de programación en español",
        epilog="Ejemplos: avadia programa.av | avadia --depurar programa.av --punto 5 | avadia --nuevo juego mi_juego",
    )
    analizador.add_argument("archivo", nargs="?", help="Archivo de código .av")
    grupo = analizador.add_mutually_exclusive_group()
    grupo.add_argument("--tokens", action="store_true", help="Mostrar los tokens")
    grupo.add_argument("--ast", action="store_true", help="Mostrar el árbol sintáctico")
    grupo.add_argument("--formatear", action="store_true", help="Mostrar el código con sangría corregida (use --escribir para guardarlo)")
    grupo.add_argument("--depurar", action="store_true", help="Ejecutar en modo depuración (puntos de interrupción y paso a paso)")
    grupo.add_argument("--nuevo", nargs=2, metavar=("TIPO", "CARPETA"), help="Crear un proyecto desde una plantilla (basico, juego, web)")
    grupo.add_argument("--paquete", nargs="+", metavar="ACCION", help="instalar RUTA | listar | quitar NOMBRE (usa --proyecto)")
    grupo.add_argument("--recursos", action="store_true", help="Listar los recursos del proyecto")
    grupo.add_argument("--ayuda", action="store_true", help="Mostrar la ayuda rápida del lenguaje")
    grupo.add_argument("--editor", action="store_true", help="Abrir Avadia Creator Studio")
    grupo.add_argument("--verificar", action="store_true", help="Revisar el programa sin ejecutarlo (errores semánticos y advertencias)")
    analizador.add_argument("--punto", type=int, action="append", default=[], metavar="N", help="Punto de interrupción en la línea N (con --depurar)")
    analizador.add_argument("--escribir", action="store_true", help="Guardar el resultado de --formatear en el archivo")
    analizador.add_argument("--proyecto", default=".", help="Carpeta del proyecto para --paquete y --recursos")
    analizador.add_argument("--version", action="version", version=f"Avadia {VERSION}")
    return analizador


def principal(argumentos=None):
    analizador = _crear_parser()
    opciones = analizador.parse_args(argumentos)
    proyecto = Path(opciones.proyecto).resolve()

    if opciones.ayuda:
        Interprete(salida=print)._mostrar_ayuda()
        return 0

    if opciones.editor:
        from editor.creador_studio import main as abrir_editor
        carpeta = Path(opciones.archivo).resolve().parent if opciones.archivo else None
        return abrir_editor(carpeta)

    if opciones.nuevo:
        from herramientas.proyectos import crear_proyecto, ErrorProyecto
        tipo, carpeta = opciones.nuevo
        try:
            destino = crear_proyecto(tipo, Path(carpeta))
        except ErrorProyecto as error:
            print(f"Error: {error}")
            return 1
        print(f"Proyecto '{tipo}' creado en {destino}")
        return 0

    if opciones.paquete:
        from herramientas.proyectos import instalar_paquete, listar_paquetes, quitar_paquete, ErrorProyecto
        accion, *resto = opciones.paquete
        try:
            if accion == "instalar" and len(resto) == 1:
                datos = instalar_paquete(resto[0], proyecto)
                print(f"Paquete '{datos['nombre']}' {datos['version']} instalado en {proyecto / 'paquetes'}")
            elif accion == "listar" and not resto:
                paquetes = listar_paquetes(proyecto)
                print("\n".join(f"{n} {v}" for n, v in paquetes) or "No hay paquetes instalados.")
            elif accion == "quitar" and len(resto) == 1:
                quitar_paquete(resto[0], proyecto)
                print(f"Paquete '{resto[0]}' eliminado.")
            else:
                print("Uso: avadia --paquete instalar RUTA | listar | quitar NOMBRE")
                return 2
        except ErrorProyecto as error:
            print(f"Error: {error}")
            return 1
        return 0

    if opciones.recursos:
        from herramientas.proyectos import indexar_recursos, ErrorProyecto
        try:
            for nombre, ruta in indexar_recursos(proyecto).items():
                print(f"{nombre}  →  {ruta}")
        except ErrorProyecto as error:
            print(f"Error: {error}")
            return 1
        return 0

    if not opciones.archivo:
        analizador.print_help()
        return 2

    ruta = Path(opciones.archivo).resolve()
    try:
        codigo = ruta.read_text(encoding="utf-8")
        if opciones.formatear:
            from herramientas.formateador import formatear
            resultado = formatear(codigo)
            if opciones.escribir:
                ruta.write_text(resultado, encoding="utf-8")
                print(f"Código formateado y guardado en {ruta}")
            else:
                print(resultado, end="")
            return 0
        tokens = Lexer(codigo).tokenizar()
        if opciones.verificar:
            return 0 if verificar(Parser(tokens).analizar(), ruta, informar_si_todo_bien=True) else 1
        if opciones.tokens:
            for token in tokens:
                print(token)
            return 0
        arbol = Parser(tokens).analizar()
        if opciones.ast:
            print(json.dumps(a_datos(arbol), ensure_ascii=False, indent=2))
            return 0
        if not verificar(arbol, ruta):
            return 1
        motor = Interprete()
        if opciones.depurar:
            from herramientas.depurador import Depurador, DepuracionCancelada
            motor.depurador = Depurador(puntos=opciones.punto, pausar_al_inicio=True)
            print("Depurador de Avadia. Escribe h para ver los comandos.")
            try:
                motor.ejecutar(arbol, archivo_actual=ruta)
            except DepuracionCancelada:
                print("Depuración terminada.")
            return 0
        motor.ejecutar(arbol, archivo_actual=ruta)
        return 0
    except AvadiaError as error:
        imprimir_error(error, ruta)
        return 1
    except OSError as error:
        print(f"ERROR DE ARCHIVO: {error}")
        return 1
    except KeyboardInterrupt:
        print("\nPrograma interrumpido.")
        return 130
    except Exception as error:  # red de seguridad: nunca mostrar un traceback al usuario
        print(f"ERROR INTERNO DE AVADIA: {type(error).__name__}: {error}")
        print("Si el problema se repite, comunícalo con el código que lo produce.")
        return 1


if __name__ == "__main__":
    sys.exit(principal())
