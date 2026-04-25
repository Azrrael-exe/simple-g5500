# Simple G5500 Controller

Control del rotor G5500 usando Arduino y CLI en Python.

## 🎯 Características

- Control de azimut y elevación por comandos
- Protocolo LLP (Low Level Protocol) para comunicación serial
- CLI en Python con dos modos de uso:
  - **Script standalone** con `uv run` (sin instalación)
  - **Paquete instalable** con entorno virtual

## 🚀 Uso Rápido (Sin Instalación)

La forma más rápida de empezar es usando el script standalone con `uv`:

```bash
# Ver ayuda
uv run cli/g5500_cli.py --help

# Listar puertos disponibles
uv run cli/g5500_cli.py ports

# Controlar motores (puedes enviar un eje o ambos)
uv run cli/g5500_cli.py move --az forward
uv run cli/g5500_cli.py move --el backward --az stop
uv run cli/g5500_cli.py move --az stop

# Leer telemetría (sensores)
uv run cli/g5500_cli.py read --type all

# Secuencia de prueba autónoma
uv run cli/g5500_cli.py test

# Modo interactivo (recomendado)
uv run cli/g5500_cli.py interactive
```

### Ventajas del Script Standalone

✅ **No requiere instalación** - solo necesitas `uv` instalado  
✅ **Dependencias automáticas** - `uv` las descarga al ejecutar  
✅ **Un solo archivo** - fácil de distribuir y ejecutar  
✅ **Portátil** - funciona en cualquier sistema con `uv`

### Instalar uv (si no lo tienes)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 📦 Uso con Pip tradicional (Opcional)

Si prefieres no usar `uv`, puedes instalar las dependencias con `pip` y ejecutar el archivo directamente desde su directorio:

```bash
cd cli
pip install -r requirements.txt

# Ahora puedes ejecutar el script:
python g5500_cli.py --help
python g5500_cli.py interactive
```

## 🎮 Modo Interactivo

El modo interactivo te permite controlar el rotor en tiempo real analizando de forma visual el feedback de los sensores:

```bash
uv run cli/g5500_cli.py interactive
```

Controles disponibles dentro de la terminal:
- `Flecha Izquierda / Derecha` - Mueve en Azimut.
- `Flecha Arriba / Abajo` - Mueve en Elevación.
- `Barra Espaciadora` - Stop (Frena ambos motores de emergencia).
- `q` o `ESC` - Salir del modo interactivo.

## 🔌 Hardware

### Pinout (Arduino)

Definido en `src/pinout.h`:

```cpp
// Azimut
AZIMUTH_PWM_PIN      = 10
AZIMUTH_DIR_PIN      = 3
AZIMUTH_SENSOR_PIN   = A0

// Elevación
ELEVATION_PWM_PIN    = 9
ELEVATION_DIR_PIN    = 2
ELEVATION_SENSOR_PIN = A1
```

### Configuración Serial

- **Baudrate**: 115200
- **Protocolo**: LLP (Low Level Protocol)
- **Detección automática** del puerto Arduino

## 📡 Protocolo de Comunicación

El sistema usa el protocolo LLP con el siguiente formato:

```
[0x7E] [LENGTH] [HEADER] [MSB] [LSB] [CHECKSUM]
```

### Headers y Sus Comandos

El firmware clasifica los comandos mediante "Headers" para identificar a qué subsistema va dirigido. Existen varios niveles de interacción ordenados por prioridad de procesamiento:

#### 1. Comandos de Sistema (Prioridad Máxima)
Se procesan antes que cualquier otra orden, detienen movimientos actuales e invalidan objetivos anteriores.
- **Header:** `0xFF` (SYSTEM_HEADER)
- **Comandos:**
  - `0x01` (SYSTEM_KILL): Parada de emergencia. Detiene los motores instantáneamente y cancela cualquier comando GOTO activo.

#### 2. Control Manual (Prioridad Alta)
Si se envían comandos manuales, se cancelarán inmediatamente los modos "GOTO".
- **Header Azimut:** `0xAA`
  - `0xA0` - Stop (Detener giro azimut)
  - `0xA1` - Forward (Giro azimut horario)
  - `0xA2` - Backward (Giro azimut antihorario)
- **Header Elevación:** `0xBB`
  - `0xB0` - Stop (Detener giro elevación)
  - `0xB1` - Forward (Giro elevación arriba)
  - `0xB2` - Backward (Giro elevación abajo)

#### 3. Control de Posición Absoluta (GOTO - Prioridad Media)
Mueve el rotor automáticamente a un ángulo específico usando un control del tipo "bang-bang" con una banda muerta (deadband). Funciona recibiendo un número entero equivalente a `grados * 10` (resolución de 0.1°).
- **Comandos (Actúan como Headers en formato clave-valor):**
  - `0xDA` (GOTO_AZIMUTH) - Ir a posición de azimut (ej. enviando `1800` para 180.0°)
  - `0xDB` (GOTO_ELEVATION) - Ir a posición de elevación

#### 4. Telemetría y Feedback (Prioridad Baja)
Se encargan de consultar el estado de los sensores.
- **Header:** `0xCC` (FEEDBACK_HEADER)
- **Comandos:**
  - `0xC0` (READ_VOLTAGE) - Solicita los voltajes crudos de azimut y elevación.
  - `0xC1` (READ_ANGLE) - Solicita los ángulos calculados tras aplicar la calibración.
  - `0xC2` (READ_ALL) - Solicita voltajes y ángulos en un solo paquete.

### Respuestas de Feedback

El rotor responde con paquetes que usan los siguientes identificadores:
- `0xAA` y `0xBB` para los valores de voltaje (en milivoltios).
- `0xAB` y `0xBC` para los valores de ángulo (`grados * 10`).

### Ejemplo

Comando de Stop Manual para Azimut:
```
0x7E 0x03 0xAA 0x00 0xA0 [CHECKSUM]
```

## 🛠️ Desarrollo

### Compilar Firmware

```bash
pio run
pio run --target upload
```

### Estructura del Proyecto

```
simple-g5500/
├── src/
│   ├── main.cpp                    # Firmware principal
│   ├── pinout.h                    # Definición de pines
│   ├── protocol.h                  # Definición del protocolo
│   └── axis_controller/
│       ├── axis_controller.h       # Control de ejes
│       └── axis_controller.cpp
└── cli/                            # Herramientas de control CLI en Python
    ├── g5500_cli.py                # Script ejecutable principal mediante Click
    ├── interactive_ui.py           # Dashboard interactivo para terminal
    ├── protocol.py                 # Encondeador de byts del protocolo LLP
    ├── serial_comm.py              # Abstracción de PySerial
    ├── README.md                   # Documentación específica
    └── requirements.txt            # Dependencias
```

## 📝 Ejemplos

### Ejemplo 1: Comandos básicos

```bash
uv run cli/g5500_cli.py move --az forward
sleep 5
uv run cli/g5500_cli.py move --az stop
```

### Ejemplo 2: Con puerto específico

```bash
# macOS
uv run cli/g5500_cli.py move --az forward --port /dev/cu.usbserial-1234

# Linux
uv run cli/g5500_cli.py move --az forward --port /dev/ttyUSB0

# Windows
uv run cli/g5500_cli.py move --az forward --port COM3
```

### Ejemplo 3: Script de automatización de test

```bash
#!/bin/bash
# Secuencia de movimientos llamando al submódulo python
uv run cli/g5500_cli.py move --az forward
sleep 3
uv run cli/g5500_cli.py move --az stop --el forward
sleep 2
uv run cli/g5500_cli.py move --el stop
```

### Ejemplo 4: Como código fuente de Python

Para instanciarlo programáticamente en tus binarios Python:

```python
#!/usr/bin/env python3
import sys
import time

# Referenciar subcarpeta temporalmente
sys.path.append('cli')

from serial_comm import G5500Serial
from protocol import LLPProtocol, AZIMUTH_HEADER, AZIMUTH_COMMANDS

with G5500Serial() as g5500:
    # Forward AZ
    packet = LLPProtocol.create_packet(AZIMUTH_HEADER, AZIMUTH_COMMANDS['forward'])
    g5500.send_packet(packet)
    time.sleep(5)
    
    # Stop AZ
    packet = LLPProtocol.create_packet(AZIMUTH_HEADER, AZIMUTH_COMMANDS['stop'])
    g5500.send_packet(packet)
```

## 🐛 Troubleshooting

### Arduino no detectado

1. Verifica la conexión USB
2. Lista puertos: `uv run cli/g5500_cli.py ports`
3. Especifica el puerto manualmente: `--port /dev/ttyUSB0`

### Error de permisos (Linux)

```bash
sudo usermod -a -G dialout $USER
# Cierra sesión y vuelve a iniciar
```

### El motor no responde

1. Verifica que el firmware esté cargado: `pio run --target upload`
2. Comprueba el baudrate (debe ser 115200)
3. Revisa las conexiones de hardware

## 📚 Documentación Adicional

- [`cli/README.md`](cli/README.md) - Documentación específica de los módulos en Python.
- [`cli/QUICKSTART.md`](cli/QUICKSTART.md) - Guía rápida

## 🤝 Contribuir

Mejoras y pull requests son bienvenidos!

## 📄 Licencia

Este proyecto está bajo licencia MIT.

