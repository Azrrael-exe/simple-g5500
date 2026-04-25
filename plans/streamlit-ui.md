# Plan: UI Streamlit para Controlador G5500

## Contexto

El proyecto ya cuenta con un CLI Python funcional ([cli/g5500_cli.py](../cli/g5500_cli.py)) que controla el rotor de antena G5500 vía serial usando el protocolo LLP. La lógica está bien separada en módulos reutilizables:

- [cli/protocol.py](../cli/protocol.py) — `LLPProtocol.create_packet()` y constantes de comandos
- [cli/serial_comm.py](../cli/serial_comm.py) — clase `G5500Serial` con context manager, auto-detección de puerto, envío y lectura/parseo de feedback
- [cli/interactive_ui.py](../cli/interactive_ui.py) — modo interactivo por teclado (referencia de patrones de control en tiempo real)

El CLI obliga al usuario a estar en una terminal y a recordar flags. Una UI web Streamlit aporta:
- Control visual con botones y feedback en tiempo real (voltaje, ángulo)
- Selección de puerto desde un dropdown poblado dinámicamente
- Botón de parada de emergencia siempre visible
- Acceso desde cualquier dispositivo en la red local (útil para operar el rotor lejos del PC)

**Objetivo**: añadir una UI Streamlit reutilizando los módulos `protocol.py` y `serial_comm.py` sin duplicar lógica.

## Archivos a crear / modificar

### Nuevo: `cli/streamlit_app.py`
App Streamlit única. Inline script metadata (PEP 723) igual que el CLI para mantener `uv run`:

```python
# /// script
# requires-python = ">=3.7"
# dependencies = [
#     "streamlit>=1.30",
#     "pyserial>=3.5",
# ]
# ///
```

### Modificar: `cli/README.md`
Añadir sección documentando cómo lanzar la UI: `uv run streamlit run streamlit_app.py`.

No se modifica ningún módulo existente.

## Diseño de la UI

### Estado de sesión (`st.session_state`)
- `g5500`: instancia persistente de `G5500Serial` (no usar context manager — la UI es de larga duración)
- `connected`: bool
- `port`: str | None
- `last_feedback`: dict con últimos valores leídos
- `command_log`: list[str] — últimos N comandos enviados (para mostrar historial)

### Layout (sidebar + main)

**Sidebar — Conexión**
- Dropdown poblado por `G5500Serial.list_ports()` con opción "Auto-detect"
- Botón **Connect** → instancia `G5500Serial(port=...)`, llama `.connect()`, guarda en session_state
- Botón **Disconnect** → `.disconnect()`
- Indicador de estado (verde/rojo) con puerto activo

**Main — Control de movimiento** (dos columnas: Azimut | Elevación)

Cada columna con tres botones:
- ◀ Backward / ⏹ Stop / ▶ Forward (azimut)
- ▼ Backward / ⏹ Stop / ▲ Forward (elevación)

Cada botón llama una función `send(header, command)` que:
1. Construye paquete con `LLPProtocol.create_packet(header, AZIMUTH_COMMANDS[cmd])`
2. Envía con `g5500.send_packet(packet)`
3. Añade entrada a `command_log`

**Botón de emergencia** (ancho completo, color rojo, siempre visible arriba)
- **🛑 STOP ALL** → envía `AZIMUTH_STOP` + `ELEVATION_STOP`

**Panel de feedback** (debajo de los controles)
- Botón **Read sensors** (tipo: voltage / angle / all vía radio)
- Métricas con `st.metric`: Azimut V, Elevación V, Azimut °, Elevación °
- Auto-refresh opcional con `st.checkbox("Auto-refresh")` + `time.sleep(1)` + `st.rerun()` cuando esté conectado

**Modo dry-run** (toggle en sidebar)
- Cuando está activo, los botones no envían — muestran los bytes hex usando `LLPProtocol.format_packet_hex()` en el log

**Log de comandos** (expander al final)
- Muestra los últimos 20 comandos: timestamp + nombre + bytes hex

## Funciones reutilizadas (NO reimplementar)

| Funcionalidad | Origen |
|---|---|
| Crear paquete LLP | `LLPProtocol.create_packet()` en [cli/protocol.py:84](../cli/protocol.py#L84) |
| Format hex | `LLPProtocol.format_packet_hex()` en [cli/protocol.py:111](../cli/protocol.py#L111) |
| Listar puertos | `G5500Serial.list_ports()` en [cli/serial_comm.py:60](../cli/serial_comm.py#L60) |
| Auto-detect | `G5500Serial.auto_detect_port()` en [cli/serial_comm.py:71](../cli/serial_comm.py#L71) |
| Conectar / desconectar | `G5500Serial.connect()` / `.disconnect()` en [cli/serial_comm.py:97](../cli/serial_comm.py#L97) |
| Enviar paquete | `G5500Serial.send_packet()` en [cli/serial_comm.py:144](../cli/serial_comm.py#L144) |
| Leer feedback | `G5500Serial.read_response()` en [cli/serial_comm.py:188](../cli/serial_comm.py#L188) |
| Constantes / mapas de comandos | `AZIMUTH_COMMANDS`, `ELEVATION_COMMANDS`, `FEEDBACK_COMMANDS`, headers |

## Consideraciones

- **No usar context manager** (`with G5500Serial() as ...`) en Streamlit: la conexión debe persistir entre re-renders. Conectar/desconectar explícitamente y guardar en `session_state`.
- **Re-runs de Streamlit**: cada interacción re-ejecuta el script. La conexión en `session_state` evita reconexiones (cada `connect()` espera 2s por reset del Arduino — sería inviable).
- **Concurrencia**: Streamlit es single-threaded por sesión; no se necesitan locks para el puerto serial.
- **Feedback auto-refresh**: implementar con cuidado para no saturar el Arduino. Mínimo 500ms entre lecturas, y solo cuando el toggle esté activado.
- **Errores**: capturar `SerialConnectionError` en cada operación y mostrar con `st.error()` en lugar de cerrar la app.

## Verificación

1. Sin Arduino conectado:
   - `uv run streamlit run cli/streamlit_app.py`
   - Activar dry-run, presionar botones → verificar que el log muestra los mismos bytes que `uv run g5500_cli.py move --az forward --dry-run`
2. Con Arduino conectado:
   - Connect → debe mostrar puerto detectado
   - Botón Forward azimut → motor responde, comando aparece en log
   - STOP ALL → ambos ejes paran
   - Read sensors → métricas actualizan con voltajes/ángulos plausibles
3. Desconectar y reconectar varias veces sin reiniciar la app → no debe haber errores de "port already in use"
4. Comparar bytes enviados vs los del CLI con `--verbose` para confirmar paridad de protocolo
