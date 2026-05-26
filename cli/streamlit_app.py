# /// script
# requires-python = ">=3.7"
# dependencies = [
#     "streamlit>=1.30",
#     "pyserial>=3.5",
# ]
# ///

import time
import streamlit as st

# Import existing modules
from protocol import (
    LLPProtocol,
    AZIMUTH_HEADER,
    ELEVATION_HEADER,
    FEEDBACK_HEADER,
    AZIMUTH_COMMANDS,
    ELEVATION_COMMANDS,
    FEEDBACK_COMMANDS,
    GOTO_AZIMUTH,
    GOTO_ELEVATION
)
from serial_comm import G5500Serial, SerialConnectionError

# Configure page
st.set_page_config(
    page_title="G5500 Controller",
    page_icon="📡",
    layout="centered"
)

# Initialize Session State
if 'g5500' not in st.session_state:
    st.session_state.g5500 = None
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'port' not in st.session_state:
    st.session_state.port = None
if 'last_feedback' not in st.session_state:
    st.session_state.last_feedback = {}
if 'command_log' not in st.session_state:
    st.session_state.command_log = []

# CSS for large stop button
st.markdown("""
<style>
div.stButton > button.stop-button {
    background-color: #ff4b4b;
    color: white;
    font-weight: bold;
    height: 3rem;
    width: 100%;
}
div.stButton > button.stop-button:hover {
    background-color: #ff3333;
    border-color: #ff3333;
}
</style>
""", unsafe_allow_html=True)


def send_command(header, command_name):
    """Constructs and sends an LLP packet."""
    try:
        if header == AZIMUTH_HEADER:
            cmd_byte = AZIMUTH_COMMANDS[command_name]
        elif header == ELEVATION_HEADER:
            cmd_byte = ELEVATION_COMMANDS[command_name]
        else:
            return

        packet = LLPProtocol.create_packet(header, cmd_byte)
        cmd_hex = LLPProtocol.format_packet_hex(packet)
        cmd_display = LLPProtocol.get_command_name(header, cmd_byte)
        timestamp = time.strftime('%H:%M:%S')
        
        log_entry = f"[{timestamp}] {cmd_display} ({cmd_hex})"
        
        if st.session_state.dry_run:
            st.session_state.command_log.insert(0, f"[DRY RUN] {log_entry}")
        else:
            if not st.session_state.connected or not st.session_state.g5500:
                st.error("Not connected to serial port")
                return
            st.session_state.g5500.send_packet(packet)
            st.session_state.command_log.insert(0, f"[SENT] {log_entry}")
            
        # Limit log to last 20 entries
        st.session_state.command_log = st.session_state.command_log[:20]
        
    except Exception as e:
        st.error(f"Error sending command: {e}")

def send_goto_command(header, angle):
    """Constructs and sends an absolute positioning (GOTO) command."""
    try:
        command_val = int(angle * 10) & 0xFFFF
        packet = LLPProtocol.create_packet(header, command_val)
        cmd_hex = LLPProtocol.format_packet_hex(packet)
        cmd_display = LLPProtocol.get_command_name(header, command_val)
        timestamp = time.strftime('%H:%M:%S')
        
        log_entry = f"[{timestamp}] {cmd_display} ({cmd_hex})"
        
        if st.session_state.dry_run:
            st.session_state.command_log.insert(0, f"[DRY RUN] {log_entry}")
        else:
            if not st.session_state.connected or not st.session_state.g5500:
                st.error("Not connected to serial port")
                return
            st.session_state.g5500.send_packet(packet)
            st.session_state.command_log.insert(0, f"[SENT] {log_entry}")
            
        st.session_state.command_log = st.session_state.command_log[:20]
        
    except Exception as e:
        st.error(f"Error sending GoTo command: {e}")

def read_feedback():
    """Requests and reads feedback from the controller."""
    if not st.session_state.connected or not st.session_state.g5500:
        if not st.session_state.dry_run:
            st.error("Not connected to read sensors")
        return
        
    try:
        packet = LLPProtocol.create_packet(FEEDBACK_HEADER, FEEDBACK_COMMANDS['all'])
        
        st.session_state.g5500.flush_input()
        st.session_state.g5500.send_packet(packet)
        
        # Adding small delay specifically for feedback reading
        time.sleep(0.1) 
        
        response = st.session_state.g5500.read_response(timeout=1.0)
        if response:
            st.session_state.last_feedback = response
    except Exception as e:
        st.error(f"Error reading feedback: {e}")


# ==========================================
# Sidebar: Connection
# ==========================================
st.sidebar.title("Connection Settings")

# Fetch available ports
available_ports = G5500Serial.list_ports()
port_options = ["Auto-detect"] + [f"{p[0]} - {p[1]}" for p in available_ports]
selected_port_option = st.sidebar.selectbox("Select Port", port_options)

col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("Connect", disabled=st.session_state.connected, use_container_width=True):
        try:
            port_to_use = None
            if selected_port_option != "Auto-detect":
                port_to_use = selected_port_option.split(" - ")[0]
                
            st.session_state.g5500 = G5500Serial(port=port_to_use)
            with st.spinner("Connecting..."):
                st.session_state.g5500.connect()
            
            st.session_state.connected = True
            st.session_state.port = st.session_state.g5500.get_port()
            st.success(f"Connected to {st.session_state.port}")
            st.rerun()
            
        except SerialConnectionError as e:
            st.error(f"Connection Failed: {e}")
            st.session_state.g5500 = None
            st.session_state.connected = False

with col2:
    if st.button("Disconnect", disabled=not st.session_state.connected, use_container_width=True):
        if st.session_state.g5500:
            st.session_state.g5500.disconnect()
        st.session_state.g5500 = None
        st.session_state.connected = False
        st.session_state.port = None
        st.session_state.last_feedback = {}
        st.success("Disconnected")
        st.rerun()

# Connection Status
if st.session_state.connected:
    st.sidebar.success(f"🟢 Connected: {st.session_state.port}")
else:
    st.sidebar.error("🔴 Disconnected")

st.sidebar.divider()

# Dry Run
st.session_state.dry_run = st.sidebar.toggle("Dry-run mode", value=False, help="Show commands without sending them")

# ==========================================
# Main Layout
# ==========================================
st.title("📡 G5500 Controller Panel")

# Emergency Stop
st.markdown('<button class="stButton stop-button">🛑 STOP ALL AXES</button>', unsafe_allow_html=True)
# To capture the click of the custom styled button, we use standard Streamlit button and style it with markdown injected earlier. Wait, that markdown only works if we add a CSS class or target the button text. Let's do it using normal st.button but styled. Streamlit doesn't allow adding CSS classes easily to st.button. The markdown injection is a hack. Let's use a standard st.button with type="primary" and large container width.
if st.button("🛑 STOP ALL AXES", type="primary", use_container_width=True):
    send_command(AZIMUTH_HEADER, 'stop')
    send_command(ELEVATION_HEADER, 'stop')

st.divider()

# Controls
st.subheader("Movement Controls")
col_az, col_el = st.columns(2)

with col_az:
    st.markdown("### Azimuth")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("◀ BWD", key="az_bwd", use_container_width=True):
            send_command(AZIMUTH_HEADER, 'backward')
    with c2:
        if st.button("⏹ STOP", key="az_stop", use_container_width=True):
            send_command(AZIMUTH_HEADER, 'stop')
    with c3:
        if st.button("▶ FWD", key="az_fwd", use_container_width=True):
            send_command(AZIMUTH_HEADER, 'forward')

with col_el:
    st.markdown("### Elevation")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("▼ DOWN", key="el_bwd", use_container_width=True):
            send_command(ELEVATION_HEADER, 'backward')
    with c2:
        if st.button("⏹ STOP", key="el_stop", use_container_width=True):
            send_command(ELEVATION_HEADER, 'stop')
    with c3:
        if st.button("▲ UP", key="el_fwd", use_container_width=True):
            send_command(ELEVATION_HEADER, 'forward')

st.divider()

# Absolute Positioning Controls
st.subheader("Absolute Positioning (GoTo)")
goto_az_col, goto_el_col = st.columns(2)

with goto_az_col:
    az_target = st.number_input("Target Azimuth (°)", min_value=0.0, max_value=450.0, value=0.0, step=1.0)
    if st.button("GO AZIMUTH", use_container_width=True):
        send_goto_command(GOTO_AZIMUTH, az_target)

with goto_el_col:
    el_target = st.number_input("Target Elevation (°)", min_value=0.0, max_value=180.0, value=0.0, step=1.0)
    if st.button("GO ELEVATION", use_container_width=True):
        send_goto_command(GOTO_ELEVATION, el_target)

st.divider()

# Feedback Panel
st.subheader("Sensor Feedback")

auto_refresh = st.checkbox("Auto-refresh (1s)", value=False)
if st.button("Read Sensors"):
    read_feedback()

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
fb = st.session_state.last_feedback

az_angle   = f"{fb['az_angle']   / 10.0:.1f}°"   if 'az_angle'   in fb else '--'
el_angle   = f"{fb['el_angle']   / 10.0:.1f}°"   if 'el_angle'   in fb else '--'
az_voltage = f"{fb['az_voltage'] / 1000.0:.3f} V" if 'az_voltage' in fb else '--'
el_voltage = f"{fb['el_voltage'] / 1000.0:.3f} V" if 'el_voltage' in fb else '--'

with m_col1:
    st.metric("Azimuth °", az_angle)
with m_col2:
    st.metric("Elevation °", el_angle)
with m_col3:
    st.metric("Azimuth V", az_voltage)
with m_col4:
    st.metric("Elevation V", el_voltage)

# Auto-refresh loop
if auto_refresh and st.session_state.connected:
    time.sleep(1)
    read_feedback()
    st.rerun()

st.divider()

# Command Log Expander
with st.expander("Command Log", expanded=True):
    if not st.session_state.command_log:
        st.write("No commands sent yet.")
    else:
        for log in st.session_state.command_log:
            st.text(log)

if __name__ == "__main__":
    import sys
    from streamlit.web import cli as stcli
    import streamlit.runtime
    
    if not streamlit.runtime.exists():
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
