# AVADIA 1.2.0 (Creator)

**Un lenguaje de programación con sintaxis en español, interpretado mediante Python.**

Avadia 1.1 amplía Avadia 1.0 con dos bibliotecas iniciales:

- **Juego 2D:** ventanas, dibujo de rectángulos, círculos y texto, lectura de teclas y actualización por fotogramas. Utiliza `tkinter` (incluido normalmente con Python para Windows).
- **Web:** construcción de páginas HTML, estilos CSS, botones, imágenes, guardado de archivos y servidor local.

## Propósito

Avadia es un lenguaje de propósito general orientado al aprendizaje, la automatización y la creación de proyectos. Esta versión permite empezar con pequeños juegos 2D de escritorio y páginas web estáticas.

## Instalar en Windows

1. Instala Python 3.10 o superior desde https://www.python.org/downloads/.
2. En el instalador de Python, activa **Add Python to PATH**. Para juegos 2D, incluye **tcl/tk and IDLE**.
3. Extrae el ZIP completo.
4. Ejecuta `instalar_avadia.bat`.
5. Abre una terminal nueva y ejecuta `avadia --version`.

Para quitarlo, ejecuta `desinstalar_avadia.bat`.

## Ejecutar ejemplos

```bat
avadia programas\hola.av
avadia programas\web\crear_sitio.av
avadia programas\juego\mover_cuadro.av
```

El ejemplo web crea `programas\web\sitio\index.html`. Para publicar ese sitio solo en tu PC, ejecuta:

```bat
avadia programas\web\servidor_sitio.av
```

Abre `http://127.0.0.1:8000/index.html` en el navegador. Detén el servidor con Ctrl+C. El servidor escucha únicamente en `127.0.0.1`, no en la red pública.

## Ejecutar pruebas

```bat
python -m unittest discover -s pruebas -v
```

Avadia no necesita paquetes externos de Python para estas funciones. La biblioteca gráfica requiere que tu instalación de Python incluya Tcl/Tk.

## Novedades de Avadia 1.2 (Creator)

### Colecciones, archivos y errores
- **Diccionarios:** `crear j = {"vida": 100}`, lectura `j["vida"]`, modificación `j["vida"] = 80`, eliminación con `quitar(j, "vida")` y pertenencia con `"vida" en j`.
- **Asignación a elementos:** `lista[0] = valor` y listas anidadas `m[1][0] = valor`.
- **Archivos:** `archivo_leer`, `archivo_escribir`, `archivo_agregar`, `archivo_existe`, `carpeta_crear`, `archivo_listar`, `archivo_eliminar(ruta, "si")`, `json_leer` y `json_escribir`. Todas las rutas quedan dentro de la carpeta del programa.
- **Errores de ejecución:** archivo, línea, columna, problema y sugerencia.

### Sprites y animaciones
- `sprite_cargar`, `sprite_hoja`, `sprite_mover`, `sprite_posicion`, `sprite_escala` (1 a 8), `sprite_rotar` (múltiplos de 90°), `sprite_capa`, `sprite_eliminar`.
- `animacion_crear`, `animacion_reproducir` (también cambia de animación), `animacion_pausar`, `animacion_detener`, `animacion_velocidad`.

### Física y colisiones
- `fisica_gravedad`, `fisica_activar(sprite, ancho, alto, [masa], [forma])`, `fisica_pared`, `fisica_velocidad`, `fisica_fuerza`, `fisica_rebote`, `fisica_friccion`, `fisica_en_suelo`.
- `colision_hay(a, b)` comprueba si dos cuerpos se tocan.
- `colision_al_chocar(a, [b], función)` llama a la función al **entrar** en contacto, con los ids de los cuerpos.
- Formas: rectángulos y círculos (`forma` = `"rectangulo"` o `"circulo"`).

### Formularios web e interactividad
- `web_formulario_iniciar`, `web_campo(nombre, etiqueta, tipo, requerido, mínimo)` (tipos: `texto`, `contrasena`, `correo`, `numero`), `web_casilla`, `web_formulario_enviar`.
- La validación se hace en el navegador con mensajes en español. Al enviar un formulario válido, se descarga un archivo JSON con los datos.
- `web_bloque_iniciar`, `web_bloque_cerrar` y `web_boton_accion(texto, bloque, "mostrar" | "ocultar" | "alternar")`.

### Avadia Creator Studio
- Abre con `avadia --editor` (o `python principal.py --editor`). Requiere tkinter.
- Editor con números de línea, resaltado de sintaxis, errores subrayados con sugerencia, autocompletado con Ctrl+Espacio, explorador de archivos, nuevo proyecto, abrir y guardar.
- Ejecutar (F5) y detener (F6) el programa, con su salida en la consola. Ver tokens y árbol sintáctico. Manual integrado y vista previa de páginas HTML.

### Ayuda desde la terminal
- `avadia --ayuda` muestra la guía rápida. `avadia --version` muestra la versión.

Compatibilidad: los programas de Avadia 1.1 siguen funcionando sin cambios.

### Herramientas (fase 4)
- **Plantillas:** `avadia --nuevo basico|juego|web CARPETA` crea un proyecto listo para usar.
- **Paquetes:** `avadia --paquete instalar RUTA` (carpeta o .zip con paquete.json), `listar`, `quitar NOMBRE`. Los módulos se importan con `importar "paquetes/NOMBRE/modulo.av"`.
- **Recursos:** los archivos de `recursos/` se indexan por nombre. `recurso("jugador")` devuelve su ruta. `avadia --recursos` los lista.
- **Formateador:** `avadia --formatear archivo.av` (o `--escribir` para guardarlo). Corrige sangría y espacios; no cambia el significado del programa (lo comprueban las pruebas). No normaliza los espacios dentro de las instrucciones.
- **Depurador:** `avadia --depurar archivo.av --punto N`. Dentro de la pausa: `c` continuar, `p` paso, `n` siguiente, `s` salir de la función, `b N` punto de interrupción, `v` variables, `pila`, `e EXPRESIÓN`, `q` terminar. Un punto solo se activa en una línea que tenga instrucciones.
- **Componentes web:** `web_componente`/`web_usar` (los valores se escapan), `web_menu`, `web_tarjeta` y bloques con diseño `"tarjetas"` (rejilla).

## Pruebas
```bat
python -m unittest discover -s pruebas -v
```
Las pruebas de la interfaz (Creator Studio) se omiten si no hay entorno gráfico. En Linux, para ejecutarlas: `xvfb-run -a python3 -m unittest discover -s pruebas -v`.

### Fase 5: audio, mapas, cámara y sprites avanzados
- **Audio:** `sonido_reproducir`, `musica_reproducir` (en bucle), `musica_pausar`, `musica_reanudar`, `musica_detener`. En Windows usa winsound con estos límites: solo WAV; un sonido a la vez (un efecto corta la música); **sin volumen** (`musica_volumen` avisa que no está disponible) y la pausa reinicia la música al reanudar.
- **Mapas en mosaicos:** `mapa_crear`, `mapa_tileset`, `mapa_bloque`, `mapa_obtener`, `mapa_solido`, `mapa_colisiones`, `mapa_guardar`, `mapa_cargar` (formato JSON, hasta 8 capas). Los mosaicos sólidos generan suelos y paredes para la física automáticamente.
- **Cámara 2D:** `camara_seguir(sprite)` centra la vista en el sprite y la limita a los bordes del mapa; `camara_mover`, `camara_posicion`. La cámara desplaza sprites y mapas; las figuras dibujadas con `juego_rectangulo` y similares no se desplazan.
- **Transparencia de sprites:** los PNG con transparencia se respetan. `sprite_transparencia(id, 0.5)` mezcla el sprite con el color de fondo: es una aproximación válida cuando el fondo es un color sólido.
- **Rotación libre:** `sprite_rotar` acepta cualquier ángulo (en grados).

### Avadia Creator (aplicación de escritorio)
- Doble clic en **AvadiaCreator.pyw** (o el acceso directo del escritorio que crea el instalador): abre el editor sin ventana de terminal. Desde ahí puedes abrir, escribir, guardar, ejecutar (F5), detener (F6), formatear, depurar y gestionar proyectos.
- Si la aplicación no arranca, revisa el archivo `avadia_creator_error.log` en tu carpeta de usuario.

## Pendiente (no incluido en 1.2)
- Depurador visual dentro del editor (hoy se usa en una terminal aparte).
- Efectos de sonido simultáneos, volumen y formatos distintos de WAV en Windows.
- Opacidad real de sprites sobre fondos que no son de color sólido.
- Cámara que desplace también las figuras dibujadas a mano.
- Paquetes desde un repositorio en línea y gestor de recursos con panel propio en el editor.



## Avadia 1.3 — Fase 1 (núcleo)
- Errores unificados para léxico, sintaxis, semántica y ejecución.
- Registro de bibliotecas: se pueden añadir funciones sin modificar el intérprete.
- Tipos opcionales: `crear edad: entero = 20`.
- Análisis semántico antes de ejecutar y el comando `avadia --verificar`.
Detalles y límites en `documentacion/fase1_nucleo.md`.
