"""
G5500 LLP Protocol Implementation

This module implements the Low Level Protocol (LLP) used to communicate
with the G5500 controller over serial connection.

Protocol Format:
    [0x7E] [LENGTH] [HEADER] [MSB] [LSB] [CHECKSUM]

Example:
    >>> protocol = LLPProtocol()
    >>> packet = protocol.create_packet(AZIMUTH_HEADER, AZIMUTH_FORWARD)
    >>> print(packet.hex())
    '7e03aa00a1...'
"""

from typing import List

# Protocol constants
START_BYTE = 0x7E
PACKET_LENGTH = 0x03

# Azimuth constants
AZIMUTH_HEADER = 0xAA
AZIMUTH_STOP = 0xA0
AZIMUTH_FORWARD = 0xA1
AZIMUTH_BACKWARD = 0xA2

# Elevation constants
ELEVATION_HEADER = 0xBB
ELEVATION_STOP = 0xB0
ELEVATION_FORWARD = 0xB1
ELEVATION_BACKWARD = 0xB2

# Feedback constants
FEEDBACK_HEADER = 0xCC
READ_VOLTAGE = 0xC0
READ_ANGLE = 0xC1
READ_ALL = 0xC2

# GoTo constants
GOTO_AZIMUTH = 0xDA
GOTO_ELEVATION = 0xDB

# System constants (max priority)
SYSTEM_HEADER = 0xFF
SYSTEM_KILL = 0x01
SYSTEM_HOME = 0x02

# Command name mappings
AZIMUTH_COMMANDS = {
    'stop': AZIMUTH_STOP,
    'forward': AZIMUTH_FORWARD,
    'backward': AZIMUTH_BACKWARD,
}

ELEVATION_COMMANDS = {
    'stop': ELEVATION_STOP,
    'forward': ELEVATION_FORWARD,
    'backward': ELEVATION_BACKWARD,
}

FEEDBACK_COMMANDS = {
    'voltage': READ_VOLTAGE,
    'angle': READ_ANGLE,
    'all': READ_ALL,
}

SYSTEM_COMMANDS = {
    'kill': SYSTEM_KILL,
    'home': SYSTEM_HOME,
}


class LLPProtocol:
    """
    Low Level Protocol implementation for G5500 controller.

    This class handles packet creation according to the LLP specification.
    Each packet contains a header, command data, and checksum for verification.
    """

    @staticmethod
    def calculate_checksum(data: List[int]) -> int:
        """
        Calculate LLP checksum.

        Args:
            data: List of bytes to calculate checksum for

        Returns:
            Checksum byte (0xFF - sum of all bytes)
        """
        total = sum(data) & 0xFF
        return (0xFF - total) & 0xFF

    @staticmethod
    def create_packet(header: int, command: int) -> bytes:
        """
        Create an LLP packet.

        Args:
            header: Header byte (AZIMUTH_HEADER or ELEVATION_HEADER)
            command: Command byte (e.g., AZIMUTH_FORWARD, ELEVATION_STOP)

        Returns:
            Complete packet as bytes ready to send over serial

        Example:
            >>> protocol = LLPProtocol()
            >>> packet = protocol.create_packet(AZIMUTH_HEADER, AZIMUTH_FORWARD)
        """
        # Build payload: [HEADER, MSB, LSB]
        val = command & 0xFFFF
        msb = (val >> 8) & 0xFF
        lsb = val & 0xFF
        payload = [header, msb, lsb]

        # Calculate checksum of payload
        checksum = LLPProtocol.calculate_checksum(payload)

        # Build complete packet: [START, LENGTH, PAYLOAD..., CHECKSUM]
        packet = [START_BYTE, PACKET_LENGTH] + payload + [checksum]

        return bytes(packet)

    @staticmethod
    def format_packet_hex(packet: bytes) -> str:
        """
        Format packet as hexadecimal string for display.

        Args:
            packet: Packet bytes

        Returns:
            Formatted hex string like "0x7E 0x03 0xAA 0x00 0xA1 0xF4"
        """
        return ' '.join(f'0x{b:02X}' for b in packet)

    @staticmethod
    def get_command_name(header: int, command: int) -> str:
        """
        Get human-readable command name.

        Args:
            header: Header byte
            command: Command byte

        Returns:
            Command name like "Azimuth Forward" or "Elevation Stop"
        """
        if header == AZIMUTH_HEADER:
            axis = "Azimuth"
            cmd_map = {v: k for k, v in AZIMUTH_COMMANDS.items()}
        elif header == ELEVATION_HEADER:
            axis = "Elevation"
            cmd_map = {v: k for k, v in ELEVATION_COMMANDS.items()}
        elif header == FEEDBACK_HEADER:
            axis = "Feedback"
            cmd_map = {v: k for k, v in FEEDBACK_COMMANDS.items()}
        elif header == SYSTEM_HEADER:
            axis = "System"
            cmd_map = {v: k for k, v in SYSTEM_COMMANDS.items()}
        elif header == GOTO_AZIMUTH:
            val = command if command < 32768 else command - 65536
            return f"Azimuth GoTo {val / 10.0}°"
        elif header == GOTO_ELEVATION:
            val = command if command < 32768 else command - 65536
            return f"Elevation GoTo {val / 10.0}°"
        else:
            return f"Unknown (0x{header:02X}, 0x{command:04X})"

        cmd_name = cmd_map.get(command, f"Unknown(0x{command:04X})")
        return f"{axis} {cmd_name.capitalize()}"
