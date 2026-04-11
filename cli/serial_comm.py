"""
Serial Communication Module for G5500 Controller

This module handles serial communication with the Arduino running
the G5500 controller firmware.
"""

import time
from typing import List, Optional, Tuple
import serial
import serial.tools.list_ports


class SerialConnectionError(Exception):
    """Raised when serial connection fails."""
    pass


class G5500Serial:
    """
    Serial communication handler for G5500 controller.

    This class manages the serial connection to the Arduino and provides
    methods to send commands and manage the connection lifecycle.

    Attributes:
        port: Serial port path (e.g., '/dev/ttyUSB0', 'COM3')
        baudrate: Communication baudrate (default: 115200)
        timeout: Read timeout in seconds (default: 1)
    """

    DEFAULT_BAUDRATE = 115200
    DEFAULT_TIMEOUT = 1.0
    WRITE_DELAY = 0.05  # Small delay between writes

    def __init__(self, port: Optional[str] = None, baudrate: int = DEFAULT_BAUDRATE,
                 timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize serial connection handler.

        Args:
            port: Serial port path. If None, will attempt auto-detection
            baudrate: Communication baudrate
            timeout: Read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    @staticmethod
    def list_ports() -> List[Tuple[str, str]]:
        """
        List all available serial ports.

        Returns:
            List of tuples (port_path, port_description)
        """
        ports = serial.tools.list_ports.comports()
        return [(port.device, port.description) for port in ports]

    @staticmethod
    def auto_detect_port() -> Optional[str]:
        """
        Attempt to auto-detect Arduino serial port.

        Looks for common Arduino USB identifiers in port descriptions.

        Returns:
            Port path if found, None otherwise
        """
        ports = serial.tools.list_ports.comports()

        # Keywords that might indicate an Arduino
        arduino_keywords = ['USB', 'ACM', 'usbserial', 'UART', 'Arduino', 'CH340']

        for port in ports:
            description = port.description.upper()
            device = port.device.upper()

            # Check if any Arduino keyword is in description or device name
            for keyword in arduino_keywords:
                if keyword.upper() in description or keyword.upper() in device:
                    return port.device

        return None

    def connect(self) -> None:
        """
        Establish serial connection.

        If port is not specified, attempts auto-detection.

        Raises:
            SerialConnectionError: If connection fails or port not found
        """
        # Auto-detect port if not specified
        if self.port is None:
            self.port = self.auto_detect_port()
            if self.port is None:
                available_ports = self.list_ports()
                if available_ports:
                    ports_str = '\n'.join([f"  {p[0]} - {p[1]}" for p in available_ports])
                    raise SerialConnectionError(
                        f"Could not auto-detect Arduino port.\n"
                        f"Available ports:\n{ports_str}\n"
                        f"Please specify port manually with --port option."
                    )
                else:
                    raise SerialConnectionError(
                        "No serial ports found. Please check Arduino connection."
                    )

        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            # Give Arduino time to reset after connection
            time.sleep(2)

        except serial.SerialException as e:
            raise SerialConnectionError(
                f"Failed to open serial port '{self.port}': {e}\n"
                f"Make sure the port is not in use by another application."
            )

    def disconnect(self) -> None:
        """Close serial connection."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.serial = None

    def send_packet(self, packet: bytes) -> None:
        """
        Send a packet over serial.

        Args:
            packet: Bytes to send

        Raises:
            SerialConnectionError: If not connected or send fails
        """
        if not self.serial or not self.serial.is_open:
            raise SerialConnectionError("Not connected to serial port")

        try:
            self.serial.write(packet)
            self.serial.flush()
            time.sleep(self.WRITE_DELAY)

        except serial.SerialException as e:
            raise SerialConnectionError(f"Failed to send packet: {e}")

    def is_connected(self) -> bool:
        """
        Check if serial connection is active.

        Returns:
            True if connected, False otherwise
        """
        return self.serial is not None and self.serial.is_open

    def get_port(self) -> Optional[str]:
        """
        Get current port path.

        Returns:
            Port path or None if not connected
        """
        return self.port if self.is_connected() else None

    def flush_input(self) -> None:
        """Flush the input buffer to clear any residual data."""
        if self.serial and self.serial.is_open:
            self.serial.reset_input_buffer()

    def read_response(self, timeout: float = 1.0, debug: bool = False) -> Optional[dict]:
        """
        Read and parse response from Arduino.

        The Arduino sends responses in LLP DataPack format:
        [START_BYTE] [LENGTH] [KEY1] [MSB1] [LSB1] [KEY2] [MSB2] [LSB2] ... [CHECKSUM]

        Args:
            timeout: Read timeout in seconds
            debug: If True, print debug information

        Returns:
            Dictionary with parsed data or None if no response
        """
        if not self.serial or not self.serial.is_open:
            raise SerialConnectionError("Serial port not open")

        original_timeout = self.serial.timeout
        self.serial.timeout = timeout

        try:
            # Read start byte
            start_byte = self.serial.read(1)
            if debug:
                print(f"[DEBUG] Start byte: {start_byte.hex() if start_byte else 'EMPTY'}")

            if len(start_byte) == 0:
                if debug:
                    print("[DEBUG] No data received (timeout)")
                return None

            if start_byte[0] != 0x7E:
                if debug:
                    print(f"[DEBUG] Invalid start byte: 0x{start_byte[0]:02X} (expected 0x7E)")
                return None

            # Read length
            length_byte = self.serial.read(1)
            if debug:
                print(f"[DEBUG] Length byte: {length_byte.hex() if length_byte else 'EMPTY'}")

            if len(length_byte) == 0:
                if debug:
                    print("[DEBUG] No length byte received")
                return None

            packet_length = length_byte[0]
            if debug:
                print(f"[DEBUG] Packet length: {packet_length} bytes")

            # Read payload and checksum
            remaining_bytes = self.serial.read(packet_length + 1)  # +1 for checksum
            if debug:
                print(f"[DEBUG] Received {len(remaining_bytes)} bytes (expected {packet_length + 1})")
                print(f"[DEBUG] Raw payload + checksum: {remaining_bytes.hex()}")

            if len(remaining_bytes) < packet_length + 1:
                if debug:
                    print(f"[DEBUG] Incomplete packet: got {len(remaining_bytes)}, expected {packet_length + 1}")
                return None

            # Parse payload (key-value pairs: [KEY] [MSB] [LSB])
            result = {}
            i = 0
            while i < packet_length:
                if i + 2 < packet_length:
                    key = remaining_bytes[i]
                    msb = remaining_bytes[i + 1]
                    lsb = remaining_bytes[i + 2]

                    # Combine MSB and LSB into 16-bit value (signed)
                    value = (msb << 8) | lsb
                    if value >= 32768:  # Handle signed int16
                        value -= 65536

                    if debug:
                        print(f"[DEBUG] Key: 0x{key:02X}, Value: {value} (0x{msb:02X}{lsb:02X})")

                    # Map keys to meaningful names
                    if key == 0xAA:
                        result['az_voltage'] = value
                    elif key == 0xBB:
                        result['el_voltage'] = value
                    elif key == 0xAB:
                        result['az_angle'] = value
                    elif key == 0xBC:
                        result['el_angle'] = value

                    i += 3
                else:
                    break

            if debug:
                print(f"[DEBUG] Parsed result: {result}")

            return result if result else None

        except serial.SerialException as e:
            if debug:
                print(f"[DEBUG] Serial exception: {e}")
            return None
        except Exception as e:
            if debug:
                print(f"[DEBUG] Unexpected exception: {e}")
            return None
        finally:
            self.serial.timeout = original_timeout
