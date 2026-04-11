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
uv run g5500.py --help

# Listar puertos disponibles
uv run g5500.py ports

# Controlar azimut
uv run g5500.py azimuth forward
uv run g5500.py azimuth backward
uv run g5500.py azimuth stop

# Controlar elevación
uv run g5500.py elevation forward
uv run g5500.py elevation backward
uv run g5500.py elevation stop

# Modo interactivo (recomendado)
uv run g5500.py interactive

# Secuencia de prueba
uv run g5500.py test
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

## 📦 Instalación Completa (Opcional)

Si prefieres instalar el CLI como paquete Python:

```bash
cd g5500_cli
./install.sh
source .venv/bin/activate

# Ahora puedes usar directamente:
g5500 --help
g5500 interactive
```

## 🎮 Modo Interactivo

El modo interactivo es la forma más cómoda de controlar el rotor:

```bash
uv run g5500.py interactive
```

Comandos disponibles:
- `az+` - Azimut adelante
- `az-` - Azimut atrás  
- `az0` - Azimut parar
- `el+` - Elevación adelante
- `el-` - Elevación atrás
- `el0` - Elevación parar
- `q` - Salir

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

### Headers

- `0xAA` - Azimut
- `0xBB` - Elevación

### Comandos

- `0xA0` / `0xB0` - Stop
- `0xA1` / `0xB1` - Forward
- `0xA2` / `0xB2` - Backward

### Ejemplo

Comando "Azimut Forward":
```
0x7E 0x03 0xAA 0x00 0xA1 [CHECKSUM]
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
├── g5500.py                        # CLI standalone (uv inline)
└── g5500_cli/                      # CLI como paquete
    ├── g5500_cli/
    │   ├── protocol.py
    │   ├── serial_comm.py
    │   └── cli.py
    └── pyproject.toml
```

## 📝 Ejemplos

### Ejemplo 1: Comandos básicos

```bash
# Con el script standalone
uv run g5500.py azimuth forward
sleep 5
uv run g5500.py azimuth stop
```

### Ejemplo 2: Con puerto específico

```bash
# macOS
uv run g5500.py --port /dev/cu.usbserial-1234 azimuth forward

# Linux
uv run g5500.py --port /dev/ttyUSB0 azimuth forward

# Windows
uv run g5500.py --port COM3 azimuth forward
```

### Ejemplo 3: Script de automatización

```bash
#!/bin/bash
# Secuencia de movimientos

uv run g5500.py azimuth forward
sleep 3
uv run g5500.py azimuth stop

uv run g5500.py elevation forward
sleep 2
uv run g5500.py elevation stop
```

### Ejemplo 4: Como librería Python

```python
#!/usr/bin/env python3
from g5500_cli.protocol import azimuth_forward, azimuth_stop
from g5500_cli.serial_comm import G5500Serial
import time

with G5500Serial() as g5500:
    g5500.send_command(azimuth_forward())
    time.sleep(5)
    g5500.send_command(azimuth_stop())
```

## 🐛 Troubleshooting

### Arduino no detectado

1. Verifica la conexión USB
2. Lista puertos: `uv run g5500.py ports`
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

- [`g5500_cli/README.md`](g5500_cli/README.md) - Documentación del CLI
- [`g5500_cli/QUICKSTART.md`](g5500_cli/QUICKSTART.md) - Guía rápida
- [`g5500_cli/examples/`](g5500_cli/examples/) - Ejemplos de código

## 🤝 Contribuir

Mejoras y pull requests son bienvenidos!

## 📄 Licencia

Este proyecto está bajo licencia MIT.

