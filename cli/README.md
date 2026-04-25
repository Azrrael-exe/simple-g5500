# G5500 Controller CLI

CLI en Python para controlar el rotor de antena G5500 a través de comunicación serial con Arduino.

## 🚀 Instalación

### Requisitos Previos

- Python 3.7 o superior
- [uv](https://docs.astral.sh/uv/) - Gestor de paquetes Python ultrarrápido
- Arduino con firmware G5500 cargado

### Instalación de uv

Si no tienes `uv` instalado:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Con pip (alternativa)
pip install uv
```

### Sin Instalación Adicional

Este CLI usa inline script metadata (PEP 723), lo que significa que **no necesitas instalar dependencias manualmente**. `uv` las gestiona automáticamente al ejecutar el script.

Simplemente clona el repositorio y ejecuta:

```bash
cd cli
uv run g5500_cli.py --help
```

¡Eso es todo! `uv` descargará e instalará automáticamente `click`, `pyserial` y `readchar` la primera vez que ejecutes el script.

## 📖 Uso

### Hacer el script ejecutable (Linux/macOS - Opcional)

```bash
chmod +x g5500_cli.py
# Luego puedes ejecutar directamente:
./g5500_cli.py --help
```

### Comandos Básicos

#### Ver ayuda

```bash
uv run g5500_cli.py --help
```

#### Listar puertos seriales disponibles

```bash
uv run g5500_cli.py ports
```

Ejemplo de salida:
```
Available serial ports:

  /dev/cu.usbserial-A50285BI
    USB Serial

  /dev/cu.Bluetooth-Incoming-Port
    Bluetooth

Auto-detected Arduino at: /dev/cu.usbserial-A50285BI
```

### Modo Interactivo (Recomendado)

El modo interactivo es la forma más cómoda de controlar el rotor en tiempo real usando el teclado:

```bash
uv run g5500_cli.py interactive
```

**Controles**:
- **← / →** - Azimut izquierda/derecha
- **↑ / ↓** - Elevación arriba/abajo
- **ESPACIO** - Detener todos los ejes
- **Q o ESC** - Salir

**Características**:
- ✅ Control en tiempo real con feedback visual
- ✅ Parada de emergencia con barra espaciadora
- ✅ Auto-detección de puerto Arduino
- ✅ Funciona en Linux, macOS y Windows

```bash
# Con puerto específico
uv run g5500_cli.py interactive --port /dev/ttyUSB0
```

**Pantalla del modo interactivo**:
```
==============================================================
G5500 Interactive Controller
==============================================================

Controls:
  ← / →       Azimuth Left/Right
  ↑ / ↓       Elevation Up/Down
  SPACE       Stop All Axes
  Q or ESC    Quit

==============================================================

Status: Azimuth: → RIGHT    | Elevation: ↑ UP
```

### Interfaz Web Streamlit (Nueva)

El proyecto cuenta con una interfaz web gráfica construida con Streamlit que te permite controlar el rotor desde el navegador, con auto-refresh de sensores y panel visual.

```bash
uv run streamlit_app.py
```

**Características**:
- Control visual con botones para azimut y elevación
- Parada de emergencia siempre visible
- Selección de puerto desde un dropdown dinámico
- Panel de métricas con voltajes y ángulos reales
- Modo dry-run para previsualización

### Comando `move` - Controlar el Rotor

El comando `move` permite controlar uno o ambos ejes del rotor.

#### Sintaxis

```bash
uv run g5500_cli.py move [OPTIONS]
```

#### Opciones

- `--az, --azimuth [forward|backward|stop]` - Comando para eje de azimut
- `--el, --elevation [forward|backward|stop]` - Comando para eje de elevación
- `--port, -p PORT` - Puerto serial (auto-detecta si no se especifica)
- `--dry-run` - Modo dry-run (muestra comandos sin enviarlos)
- `--verbose, -v` - Salida detallada

#### Ejemplos - Un Solo Eje

```bash
# Azimut adelante
uv run g5500_cli.py move --az forward

# Azimut atrás
uv run g5500_cli.py move --az backward

# Azimut parar
uv run g5500_cli.py move --az stop

# Elevación adelante
uv run g5500_cli.py move --el forward

# Elevación atrás
uv run g5500_cli.py move --el backward

# Elevación parar
uv run g5500_cli.py move --el stop
```

#### Ejemplos - Ambos Ejes Simultáneamente

```bash
# Azimut adelante y elevación detenida
uv run g5500_cli.py move --az forward --el stop

# Azimut atrás y elevación adelante
uv run g5500_cli.py move --az backward --el forward

# Ambos ejes atrás
uv run g5500_cli.py move --az backward --el backward

# Detener ambos ejes
uv run g5500_cli.py move --az stop --el stop
```

#### Ejemplos - Modo Dry-Run

El modo dry-run muestra los bytes hexadecimales exactos que se enviarían, sin realmente enviarlos. Útil para debugging o para conocer el comando manual.

```bash
# Ver qué se enviaría para azimut adelante
uv run g5500_cli.py move --az forward --dry-run
```

Salida:
```
[DRY RUN] Would send to port auto-detect:
  Azimuth Forward     : 0x7E 0x03 0xAA 0x00 0xA1 0xF4
```

```bash
# Ver comandos para ambos ejes
uv run g5500_cli.py move --az forward --el stop --dry-run
```

Salida:
```
[DRY RUN] Would send to port auto-detect:
  Azimuth Forward     : 0x7E 0x03 0xAA 0x00 0xA1 0xF4
  Elevation Stop      : 0x7E 0x03 0xBB 0x00 0xB0 0xF2
```

#### Ejemplos - Puerto Específico

Si la auto-detección no funciona o tienes múltiples Arduinos:

```bash
# Linux
uv run g5500_cli.py move --az forward --port /dev/ttyUSB0

# macOS
uv run g5500_cli.py move --az forward --port /dev/cu.usbserial-A50285BI

# Windows
uv run g5500_cli.py move --az forward --port COM3
```

#### Ejemplos - Modo Verbose

```bash
uv run g5500_cli.py move --az forward --el stop --verbose
```

Salida:
```
Connected to /dev/cu.usbserial-A50285BI
Sent Azimuth Forward: 0x7E 0x03 0xAA 0x00 0xA1 0xF4
Sent Elevation Stop: 0x7E 0x03 0xBB 0x00 0xB0 0xF2
✓ Commands sent successfully
```

### Comando `test` - Secuencia de Prueba

Ejecuta una secuencia de prueba predefinida para verificar el funcionamiento del controlador.

#### Sintaxis

```bash
uv run g5500_cli.py test [OPTIONS]
```

#### Opciones

- `--port, -p PORT` - Puerto serial (auto-detecta si no se especifica)
- `--dry-run` - Previsualizar secuencia sin ejecutarla

#### Secuencia de Prueba

1. Azimut adelante (2s)
2. Azimut parar (0.5s)
3. Elevación adelante (2s)
4. Elevación parar (0.5s)
5. Azimut atrás (2s)
6. Azimut parar (0.5s)
7. Elevación atrás (2s)
8. Elevación parar (0.5s)

#### Ejemplos

```bash
# Ejecutar secuencia de prueba
uv run g5500_cli.py test

# Previsualizar secuencia sin ejecutar
uv run g5500_cli.py test --dry-run

# Con puerto específico
uv run g5500_cli.py test --port /dev/ttyUSB0
```

**Nota**: Presiona `Ctrl+C` durante el test para abortar. El CLI enviará automáticamente comandos de parada a ambos ejes.

## 🔧 Protocolo LLP

El CLI implementa el protocolo LLP (Low Level Protocol) usado por el firmware G5500.

### Formato del Paquete

```
[START] [LENGTH] [HEADER] [MSB] [LSB] [CHECKSUM]
 0x7E     0x03     0xAA   0x00  0xA1     0xF4
```

### Headers

- `0xAA` - Azimut
- `0xBB` - Elevación

### Comandos

#### Azimut
- `0xA0` - Stop
- `0xA1` - Forward
- `0xA2` - Backward

#### Elevación
- `0xB0` - Stop
- `0xB1` - Forward
- `0xB2` - Backward

### Cálculo de Checksum

```
checksum = 0xFF - (sum(payload_bytes) & 0xFF)
```

Ejemplo para "Azimuth Forward":
```
payload = [0xAA, 0x00, 0xA1]
sum = 0xAA + 0x00 + 0xA1 = 0x14B
checksum = 0xFF - (0x14B & 0xFF) = 0xFF - 0x4B = 0xB4
```

## 🔌 Configuración de Hardware

### Conexión Serial

- **Baudrate**: 115200
- **Data bits**: 8
- **Parity**: None
- **Stop bits**: 1
- **Flow control**: None

### Pinout del Arduino

Según `src/pinout.h`:

```
Azimut:
  PWM Pin:    9
  DIR Pin:    2
  Sensor Pin: A1

Elevación:
  PWM Pin:    10
  DIR Pin:    3
  Sensor Pin: A0
```

## 📝 Ejemplos de Automatización

### Script Bash - Secuencia Personalizada

```bash
#!/bin/bash
# custom_sequence.sh

PORT="/dev/ttyUSB0"

echo "Starting custom sequence..."

# Mover azimut adelante por 5 segundos
python g5500_cli.py move --az forward --port $PORT
sleep 5
python g5500_cli.py move --az stop --port $PORT

# Pausa
sleep 1

# Mover elevación adelante por 3 segundos
python g5500_cli.py move --el forward --port $PORT
sleep 3
python g5500_cli.py move --el stop --port $PORT

echo "Sequence completed"
```

### Script Python - Control Programático

```python
#!/usr/bin/env python3
"""
Ejemplo de uso del CLI como módulo Python.
"""

import time
from protocol import LLPProtocol, AZIMUTH_HEADER, AZIMUTH_FORWARD, AZIMUTH_STOP
from serial_comm import G5500Serial

def main():
    # Conectar al Arduino
    with G5500Serial() as g5500:
        print(f"Connected to {g5500.get_port()}")

        # Crear y enviar comando
        packet = LLPProtocol.create_packet(AZIMUTH_HEADER, AZIMUTH_FORWARD)
        g5500.send_packet(packet)
        print("Azimuth moving forward...")

        # Esperar
        time.sleep(5)

        # Detener
        packet = LLPProtocol.create_packet(AZIMUTH_HEADER, AZIMUTH_STOP)
        g5500.send_packet(packet)
        print("Azimuth stopped")

if __name__ == '__main__':
    main()
```

### Envío Manual de Comandos

Si quieres enviar comandos manualmente usando herramientas como `screen`, `minicom`, o Python serial terminal, usa los bytes del modo dry-run:

```bash
# Ver los bytes a enviar
uv run g5500_cli.py move --az forward --dry-run
# Output: 0x7E 0x03 0xAA 0x00 0xA1 0xF4

# Enviar con Python
python3 -c "import serial; s=serial.Serial('/dev/ttyUSB0', 115200); s.write(bytes([0x7E, 0x03, 0xAA, 0x00, 0xA1, 0xF4]))"
```

## 🐛 Troubleshooting

### Error: "No serial ports found"

**Problema**: No se detectan puertos seriales.

**Soluciones**:
1. Verifica que el Arduino esté conectado vía USB
2. Verifica que el cable USB funcione (algunos cables solo cargan, no transmiten datos)
3. Instala los drivers USB para tu Arduino (CH340, FTDI, etc.)

### Error: "Could not auto-detect Arduino port"

**Problema**: Hay puertos disponibles pero no se auto-detecta el Arduino.

**Soluciones**:
1. Usa `uv run g5500_cli.py ports` para listar puertos
2. Especifica el puerto manualmente con `--port`

### Error: "Permission denied" (Linux)

**Problema**: No tienes permisos para acceder al puerto serial.

**Soluciones**:

```bash
# Agregar tu usuario al grupo dialout
sudo usermod -a -G dialout $USER

# Cerrar sesión y volver a iniciar, o ejecutar:
newgrp dialout

# Alternativamente, usar sudo (no recomendado)
sudo uv run g5500_cli.py move --az forward
```

### Error: "Port already in use"

**Problema**: El puerto está siendo usado por otra aplicación.

**Soluciones**:
1. Cierra otras aplicaciones que puedan estar usando el puerto (Arduino IDE, PlatformIO, otros scripts)
2. En Linux, verifica procesos: `lsof | grep ttyUSB0`
3. Mata el proceso: `sudo fuser -k /dev/ttyUSB0`

### El motor no responde

**Problema**: Los comandos se envían pero el motor no se mueve.

**Verificaciones**:
1. **Firmware correcto**: Verifica que el Arduino tenga el firmware G5500 cargado
   ```bash
   cd ..  # Volver al directorio raíz
   pio run --target upload
   ```

2. **Baudrate correcto**: El firmware usa 115200, verifica que coincida

3. **Hardware conectado**: Verifica las conexiones del motor

4. **Probar comandos básicos**: Usa el modo verbose para ver si los comandos se envían
   ```bash
   uv run g5500_cli.py move --az forward --verbose
   ```

5. **Monitor serial**: Abre el monitor serial para ver si hay mensajes de error del Arduino
   ```bash
   pio device monitor
   ```

### Comandos muy lentos

**Problema**: Cada comando tarda mucho en ejecutarse.

**Causa**: El código espera 2 segundos después de conectar para que el Arduino se reinicie.

**Solución**: Para múltiples comandos, considera:
- Usar el modo interactivo (si lo implementas más adelante)
- Crear un script Python que mantenga la conexión abierta
- Reducir el delay en `serial_comm.py` (línea con `time.sleep(2)`)

## 🔍 Estructura de Archivos

```
cli/
├── g5500_cli.py         # CLI principal con comandos Click
├── protocol.py          # Implementación del protocolo LLP
├── serial_comm.py       # Comunicación serial con Arduino
├── requirements.txt     # Dependencias Python
└── README.md           # Esta documentación
```

## 📚 Referencias

- [Click Documentation](https://click.palletsprojects.com/)
- [PySerial Documentation](https://pyserial.readthedocs.io/)
- [G5500 Controller Firmware](../src/main.cpp)
- [Protocol Definition](../src/protocol.h)

## 🤝 Contribuir

¡Mejoras y sugerencias son bienvenidas! Si encuentras algún bug o tienes ideas para nuevas funcionalidades, no dudes en contribuir.

## 📄 Licencia

Este proyecto está bajo licencia MIT.
