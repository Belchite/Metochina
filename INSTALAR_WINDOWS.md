# Metochina - Guia de Instalacion en Windows

Guia completa paso a paso para instalar y ejecutar Metochina en Windows.
No se requiere experiencia previa con Python.

---

## Paso 1: Instalar Python

1. Abre tu navegador y ve a [python.org/downloads](https://www.python.org/downloads/)
2. Haz clic en el boton amarillo que dice **"Download Python 3.1x.x"** (la version mas reciente)
3. Una vez descargado, ejecuta el instalador
4. **MUY IMPORTANTE**: En la primera pantalla del instalador, marca la casilla que dice:

   ```
   [x] Add Python to PATH
   ```

   Si no marcas esta casilla, Windows no reconocera el comando `python` y tendras que reinstalar.

5. Haz clic en **"Install Now"**
6. Espera a que termine la instalacion y cierra el instalador

## Paso 2: Verificar la instalacion

1. Abre una terminal:
   - Presiona `Windows + R`, escribe `cmd` y presiona Enter
   - O busca "Simbolo del sistema" en el menu de inicio
2. Escribe el siguiente comando y presiona Enter:

   ```
   python --version
   ```

3. Deberias ver algo como:

   ```
   Python 3.11.7
   ```

   Si ves un numero de version 3.11 o superior, la instalacion fue exitosa.

## Paso 3: Descargar el proyecto

### Opcion A: Descargar como ZIP (mas facil)

1. Ve a la pagina del repositorio en GitHub
2. Haz clic en el boton verde **"Code"**
3. Selecciona **"Download ZIP"**
4. Extrae el archivo ZIP en una carpeta de tu eleccion (por ejemplo, `C:\Users\TuUsuario\metochina`)

### Opcion B: Clonar con Git

Si tienes Git instalado, abre la terminal y ejecuta:

```
git clone https://github.com/tu-usuario/metochina.git
cd metochina
```

## Paso 4: Instalar dependencias

1. Abre la terminal (cmd o PowerShell)
2. Navega a la carpeta del proyecto:

   ```
   cd C:\Users\TuUsuario\metochina
   ```

3. Instala las dependencias necesarias:

   ```
   python -m pip install Pillow click
   ```

4. Espera a que se descarguen e instalen los paquetes.

## Paso 5: Ejecutar Metochina

### Modo interactivo (NUEVO en v1.2)

Ejecuta Metochina **sin argumentos** para abrir el menu visual interactivo:

```
python -m metochina
```

Esto abrira un menu con estilo hacker donde podras navegar con numeros:

```
[1] Escanear Imagen
[2] Escaneo por Lotes
[3] Extraer GPS
[4] Calcular Hashes
[5] Evaluacion de Riesgos
[6] Escaneo Profundo
[7] Configuracion
[0] Salir
```

### Modo CLI (clasico)

Si proporcionas argumentos, Metochina funciona como antes:

```
python -m metochina scan foto.jpg
```

### Otros ejemplos de uso

```
# Analizar una imagen con ruta completa
python -m metochina scan "C:\Users\TuUsuario\Imagenes\vacaciones.jpg"

# Analizar varias imagenes en una carpeta
python -m metochina scan carpeta_fotos/

# Exportar resultados a HTML
python -m metochina scan foto.jpg --export html

# Exportar resultados a JSON
python -m metochina scan foto.jpg --export json

# Exportar resultados a CSV
python -m metochina scan foto.jpg --export csv
```

---

## Solucion de problemas comunes

### "python" no se reconoce como comando

**Causa**: Python no se agrego al PATH durante la instalacion.

**Solucion**:
1. Desinstala Python desde "Agregar o quitar programas"
2. Vuelve a instalar Python asegurandote de marcar **"Add Python to PATH"**
3. Cierra y vuelve a abrir la terminal

### "pip" no se reconoce como comando

**Solucion**: Usa `python -m pip` en lugar de `pip`:

```
python -m pip install Pillow click
```

### Error al instalar Pillow

1. Asegurate de tener Python 3.11 o superior:
   ```
   python --version
   ```
2. Actualiza pip:
   ```
   python -m pip install --upgrade pip
   ```
3. Intenta instalar Pillow de nuevo:
   ```
   python -m pip install Pillow
   ```

### Error "ModuleNotFoundError: No module named 'metochina'"

**Causa**: No estas ejecutando el comando desde la carpeta correcta del proyecto.

**Solucion**:
```
cd C:\ruta\a\la\carpeta\metochina
python -m metochina scan foto.jpg
```

---

## Tabla resumen de comandos

| Accion                         | Comando                                      |
| ------------------------------ | -------------------------------------------- |
| Verificar version de Python    | `python --version`                           |
| Instalar dependencias          | `python -m pip install Pillow click`         |
| **Menu interactivo (NUEVO)**   | `python -m metochina`                        |
| Analizar una imagen            | `python -m metochina scan foto.jpg`          |
| Analizar una carpeta           | `python -m metochina scan carpeta/`          |
| Exportar a HTML                | `python -m metochina scan foto.jpg --export html` |
| Ver ayuda                      | `python -m metochina --help`                 |

---

## Requisitos del sistema

- **Sistema operativo**: Windows 10 o superior
- **Python**: 3.11 o superior
- **Espacio en disco**: ~50 MB (incluyendo dependencias)
- **Conexion a internet**: Solo necesaria para la instalacion inicial. El analisis funciona completamente sin conexion.
