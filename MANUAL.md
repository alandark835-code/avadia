# Manual de Avadia 1.1

## 1. Sintaxis general

```av
// Comentario de una línea
crear nombre = "Ana"
crear edad = 22
mostrar "Hola " + nombre

si edad >= 18 entonces
    mostrar "Mayor de edad"
sino
    mostrar "Menor de edad"
fin
```

Las palabras reservadas del lenguaje están en español y distinguen mayúsculas de minúsculas.

## 2. Tipos y estructuras

- Números enteros y decimales.
- Textos entre comillas simples o dobles.
- Booleanos `verdadero` y `falso`.
- Listas: `crear colores = ["rojo", "azul"]`.
- Índices: `mostrar colores[0]`.
- Asignación existente: `edad = edad + 1`.

## 3. Condiciones y operadores

```av
si edad >= 18 y edad < 65 entonces
    mostrar "Edad laboral"
fin
```

Operadores: `+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `y`, `o`, `no`, `en`.

## 4. Ciclos

```av
crear contador = 0
mientras contador < 5 hacer
    mostrar contador
    contador = contador + 1
fin

para numero en rango(1, 4) hacer
    mostrar numero
fin
```

`romper` sale del ciclo actual.

## 5. Funciones

```av
funcion sumar(a, b)
    retornar a + b
fin

crear total = sumar(10, 5)
mostrar total
```

## 6. Funciones generales integradas

- `leer(mensaje)` — solicita texto al usuario.
- `longitud(valor)` — devuelve la longitud.
- `agregar(lista, valor)` — agrega un elemento.
- `quitar(lista, indice)` — elimina y devuelve un elemento; el índice es opcional.
- `rango(fin)` o `rango(inicio, fin, paso)` — crea una secuencia de enteros.
- `texto(valor)`, `numero(valor)`, `tipo(valor)` — conversiones e inspección.
- `ayuda` — imprime una guía rápida.

## 7. Juegos 2D

Avadia 1.1 incluye un motor 2D sencillo de escritorio. Requiere que Python tenga `tkinter`/Tcl-Tk.

```av
juego_ventana(640, 420, "Mi juego")
crear jugador_x = 100
crear jugador_y = 100

funcion actualizar()
    si juego_tecla("derecha") entonces
        jugador_x = jugador_x + 4
    fin
    juego_limpiar("#18212f")
    juego_rectangulo(jugador_x, jugador_y, 40, 40, "#ef4444")
    juego_circulo(300, 160, 50, "#3b82f6")
    juego_texto(16, 16, "Mi primer juego", "#ffffff", 18)
fin

juego_iniciar(actualizar)
```

Funciones:

| Función | Descripción |
|---|---|
| `juego_ventana(ancho, alto, titulo)` | Configura la ventana. |
| `juego_iniciar(actualizar)` | Abre la ventana y llama a la función de actualización aproximadamente cada 16 ms. |
| `juego_limpiar(color)` | Limpia el fotograma y cambia el fondo. |
| `juego_rectangulo(x, y, ancho, alto, color)` | Dibuja un rectángulo. |
| `juego_circulo(x, y, diametro, color)` | Dibuja un círculo. |
| `juego_texto(x, y, texto, color, tamano)` | Dibuja texto. |
| `juego_tecla(nombre)` | Comprueba si una tecla está presionada. |

Teclas con alias: `izquierda`, `derecha`, `arriba`, `abajo`, `espacio`, `entrada`, `escape`. También se acepta el nombre de tecla de Tk, como `a` o `w`.

Los colores recomendados son valores hexadecimales, por ejemplo `"#ffffff"` para blanco y `"#000000"` para negro.

La función `actualizar` se ejecuta una vez por fotograma. El lienzo se limpia automáticamente al inicio de cada fotograma; dentro de la función se dibuja todo lo que debe permanecer visible en ese fotograma.

## 8. Páginas web

La biblioteca web genera HTML y CSS. Ejemplo:

```av
web_iniciar("Mi portafolio")
web_titulo("Hola, soy desarrollador")
web_parrafo("Este sitio fue creado usando Avadia.")
web_boton("Ver proyectos", "https://example.com/proyectos")
web_estilo("body { background: #111827; color: white; }")
web_guardar("sitio/index.html")
```

Funciones:

| Función | Descripción |
|---|---|
| `web_iniciar(titulo)` | Empieza una página nueva. |
| `web_titulo(texto)` | Añade un encabezado. |
| `web_parrafo(texto)` | Añade un párrafo. |
| `web_boton(texto, enlace)` | Añade un enlace con aspecto de botón. |
| `web_imagen(ruta, descripcion)` | Añade una imagen local o remota. |
| `web_estilo(css)` | Añade reglas CSS. |
| `web_html(codigo)` | Inserta HTML sin filtrar. Solo usar con contenido de confianza. |
| `web_guardar(ruta)` | Guarda el archivo `.html` junto al programa `.av` si la ruta es relativa. |
| `web_servidor(puerto)` | Sirve la última página guardada en `127.0.0.1` y abre el navegador. Ctrl+C detiene el servidor. |

`web_html` permite control avanzado y también puede insertar scripts. Como no filtra el HTML, no insertes contenido proporcionado por terceros sin revisarlo.

## 9. Ejecutar y depurar

```bat
avadia programas\hola.av
avadia programas\hola.av --tokens
avadia programas\hola.av --ast
avadia --version
```

## 10. Arquitectura y seguridad

- Lexer: tokeniza el código y conserva línea/columna.
- Parser: comprueba la gramática y genera nodos AST.
- Intérprete: evalúa nodos explícitamente; no usa `eval()` ni `exec()`.
- Bibliotecas: interfaces controladas para la ventana 2D y generación web.

Avadia 1.1 no es un entorno aislado. Un archivo `.av` puede leer y escribir archivos por medio de las funciones habilitadas, importar otros `.av` y ejecutar acciones en el equipo. Ejecuta solo código de confianza.

## 11. Límites de la primera biblioteca gráfica/web

- El motor 2D es una base educativa para prototipos; no es equivalente a Unity, Godot ni un motor 2D avanzado.
- No incluye física, colisiones automáticas, mapas, audio, spritesheets ni editor visual.
- La biblioteca web produce páginas HTML/CSS; no incorpora un framework de aplicaciones web, base de datos ni backend. Para lógica compleja en navegador se puede añadir código HTML/JavaScript de confianza con `web_html`.
- `web_servidor` publica únicamente en el equipo local (`127.0.0.1`), no despliega el sitio en Internet.

## 9. Novedades de Avadia 1.2

### Diccionarios
```av
crear jugador = {"nombre": "Ana", "vida": 100}
jugador["vida"] = 80
mostrar jugador["vida"]
quitar(jugador, "nombre")
```

### Listas anidadas
```av
crear tablero = [[1, 2], [3, 4]]
tablero[1][0] = 9
```

### Archivos (carpeta del proyecto)
```av
archivo_escribir("datos.txt", "Hola Avadia")
archivo_agregar("datos.txt", "Nueva línea")
crear contenido = archivo_leer("datos.txt")
json_escribir("partida.json", {"nivel": 2})
archivo_eliminar("datos.txt", "si")
```
La eliminación exige escribir `"si"` como confirmación. Las rutas que salen de la carpeta del programa se rechazan.

### Sprites y animaciones
```av
juego_ventana(640, 420, "Mi juego")
crear jugador = sprite_hoja("recursos/jugador.png", 32, 32, 100, 100)
sprite_escala(jugador, 2)
animacion_crear(jugador, "caminar", [0, 1, 2, 3], 8)
animacion_reproducir(jugador, "caminar")

funcion actualizar()
    juego_limpiar("#18212f")
fin

juego_iniciar(actualizar)
```
Los cuadros de una hoja se numeran de izquierda a derecha y de arriba abajo, empezando en 0. Las rutas de imagen también quedan dentro de la carpeta del proyecto.

Límites: no hay transparencia parcial; la rotación solo admite múltiplos de 90 grados; la escala es un entero de 1 a 8.

### Errores
Los errores de ejecución indican archivo, línea y columna, y muestran una sugerencia cuando es posible.


### Física y colisiones
```av
juego_ventana(640, 420, "Física")
crear caja = sprite_cargar("recursos/bloque.png", 100, 20)
fisica_activar(caja, 32, 32)
fisica_rebote(caja, 0.4)
crear suelo = fisica_pared(0, 380, 640, 40)

funcion al_tocar(a, b)
    mostrar "Contacto"
fin
colision_al_chocar(caja, suelo, al_tocar)

funcion actualizar()
    si juego_tecla("derecha") entonces
        fisica_fuerza(caja, 300, 0)
    fin
    juego_limpiar("#18212f")
fin

juego_iniciar(actualizar)
```
La gravedad tira hacia abajo (el eje Y crece hacia abajo). Las paredes son obstáculos estáticos. La función de colisión recibe los ids de los dos cuerpos y se llama al entrar en contacto.

Límites: los círculos detectan colisiones con su forma real, pero al empujarse contra sólidos usan su caja envolvente. No es un motor físico profesional.

### Formularios web
```av
web_iniciar("Registro")
web_titulo("Crear cuenta")
web_formulario_iniciar("registro")
web_campo("nombre", "Nombre", "texto", verdadero)
web_campo("correo", "Correo", "correo", verdadero)
web_campo("clave", "Contraseña", "contrasena", verdadero, 8)
web_casilla("acepto", "Acepto las condiciones", verdadero)
web_formulario_enviar("Registrarme")
web_guardar("sitio/index.html")
```
La validación ocurre en el navegador. Al enviar un formulario válido, el navegador descarga un archivo JSON con los datos capturados.

### Bloques que se muestran u ocultan
```av
web_bloque_iniciar("ayuda")
web_parrafo("Usa una contraseña larga.")
web_bloque_cerrar()
web_boton_accion("Mostrar ayuda", "ayuda", "alternar")
```

### Avadia Creator Studio
Abre el editor visual con `avadia --editor`. Ofrece resaltado, errores subrayados, autocompletado (Ctrl+Espacio), explorador, ejecución (F5) y detención (F6). Requiere tkinter.


### Componentes web reutilizables
```av
web_iniciar("Tienda")
web_componente("precio", "<p class=\"precio\">{producto}: {valor} €</p>")
web_usar("precio", {"producto": "Camiseta", "valor": 12})
web_menu([["Inicio", "#inicio"], ["Contacto", "contacto.html"]])
web_bloque_iniciar("productos", "tarjetas")
web_tarjeta("Juego", "Un juego de ejemplo", "recursos/juego.png")
web_bloque_cerrar()
web_guardar("sitio/index.html")
```
Los valores de `web_usar` se escapan automáticamente.

### Recursos
```av
crear imagen = recurso("jugador")
crear s = sprite_cargar(imagen, 10, 10)
```

### Depuración
```bat
avadia --depurar programa.av --punto 7
```


### Audio
```av
sonido_reproducir("recursos/salto.wav")
musica_reproducir("recursos/musica.wav")
musica_pausar()
musica_reanudar()
```
En Windows solo se reproducen archivos WAV, un sonido a la vez. El control de volumen no está disponible.

### Mapas y cámara
```av
mapa_crear(40, 12, 16)
mapa_tileset("recursos/tiles.png", 16, 16)
mapa_bloque("fondo", 0, 11, 2)
mapa_solido(2)
mapa_colisiones()

crear heroe = sprite_cargar("recursos/heroe.png", 40, 20)
fisica_activar(heroe, 16, 16)
camara_seguir(heroe)
```
Los mosaicos se numeran desde 1 de izquierda a derecha y de arriba abajo; 0 significa vacío. Usa `mapa_colisiones()` después de cambiar mosaicos sólidos (`mapa_bloque` ya lo hace automáticamente).

### Sprites: transparencia y rotación
```av
sprite_rotar(heroe, 45)
sprite_transparencia(heroe, 0.5)
```
