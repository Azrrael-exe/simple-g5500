# Inicio Rápido - G5500 CLI

Guía de inicio rápido para usar el CLI del controlador G5500.

## Instalación de uv (solo una vez)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Comandos Básicos

### 🎮 Modo Interactivo (Recomendado)

La forma más fácil y cómoda de controlar el rotor:

```bash
uv run g5500_cli.py interactive
```

**Controles del teclado**:
- `←` / `→` - Azimut izquierda/derecha
- `↑` / `↓` - Elevación arriba/abajo
- `ESPACIO` - **Detener todos los ejes** (parada de emergencia)
- `Q` o `ESC` - Salir

**Ventajas**:
- ✅ Control en tiempo real
- ✅ Feedback visual instantáneo
- ✅ Parada rápida con barra espaciadora
- ✅ Muy intuitivo

---

### Ver ayuda
```bash
uv run g5500_cli.py --help
```

### Listar puertos disponibles
```bash
uv run g5500_cli.py ports
```

### Controlar Azimut
```bash
# Adelante
uv run g5500_cli.py move --az forward

# Atrás
uv run g5500_cli.py move --az backward

# Parar
uv run g5500_cli.py move --az stop
```

### Controlar Elevación
```bash
# Adelante
uv run g5500_cli.py move --el forward

# Atrás
uv run g5500_cli.py move --el backward

# Parar
uv run g5500_cli.py move --el stop
```

### Controlar Ambos Ejes
```bash
# Ambos adelante
uv run g5500_cli.py move --az forward --el forward

# Azimut adelante, elevación parar
uv run g5500_cli.py move --az forward --el stop

# Parar ambos
uv run g5500_cli.py move --az stop --el stop
```

### Modo Dry-Run (ver bytes sin enviar)
```bash
uv run g5500_cli.py move --az forward --dry-run
```

Salida:
```
[DRY RUN] Would send to port auto-detect:
  Azimuth Forward     : 0x7E 0x03 0xAA 0x00 0xA1 0xB4
```

### Especificar Puerto Manualmente
```bash
# Linux
uv run g5500_cli.py move --az forward --port /dev/ttyUSB0

# macOS
uv run g5500_cli.py move --az forward --port /dev/cu.usbserial-XXXXXX

# Windows
uv run g5500_cli.py move --az forward --port COM3
```

### Secuencia de Prueba
```bash
# Ver secuencia sin ejecutar
uv run g5500_cli.py test --dry-run

# Ejecutar secuencia de prueba
uv run g5500_cli.py test
```

## Envío Manual de Comandos

Si quieres enviar comandos manualmente (por ejemplo, para usar en otros scripts):

1. Obtén los bytes con dry-run:
```bash
uv run g5500_cli.py move --az forward --dry-run
# Output: 0x7E 0x03 0xAA 0x00 0xA1 0xB4
```

2. Envía con Python directo:
```bash
python3 -c "import serial; s=serial.Serial('/dev/ttyUSB0', 115200); s.write(bytes([0x7E, 0x03, 0xAA, 0x00, 0xA1, 0xB4]))"
```

## Notas Importantes

- El Arduino debe tener el firmware G5500 cargado
- Baudrate: 115200
- `uv` instala las dependencias automáticamente la primera vez
- Usa `Ctrl+C` para abortar comandos
- El modo dry-run es útil para debugging

## Documentación Completa

Para más detalles, consulta [README.md](README.md)
