#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.7"
# dependencies = [
#     "pyserial>=3.5",
# ]
# ///
"""
Example usage of G5500 CLI as a Python module.

This script demonstrates how to use the protocol and serial communication
modules directly in your own Python scripts.

Usage:
    uv run example_usage.py
"""

import time
from protocol import (
    LLPProtocol,
    AZIMUTH_HEADER, ELEVATION_HEADER,
    AZIMUTH_FORWARD, AZIMUTH_STOP,
    ELEVATION_FORWARD, ELEVATION_STOP
)
from serial_comm import G5500Serial


def example_basic_movement():
    """Basic example: Move azimuth forward for 3 seconds."""
    print("Example 1: Basic movement")
    print("-" * 50)

    with G5500Serial() as g5500:
        print(f"Connected to {g5500.get_port()}")

        # Move azimuth forward
        packet = LLPProtocol.create_packet(AZIMUTH_HEADER, AZIMUTH_FORWARD)
        g5500.send_packet(packet)
        print("Azimuth moving forward...")

        time.sleep(3)

        # Stop azimuth
        packet = LLPProtocol.create_packet(AZIMUTH_HEADER, AZIMUTH_STOP)
        g5500.send_packet(packet)
        print("Azimuth stopped")

    print()


def example_both_axes():
    """Example: Control both axes simultaneously."""
    print("Example 2: Both axes movement")
    print("-" * 50)

    with G5500Serial() as g5500:
        print(f"Connected to {g5500.get_port()}")

        # Move both axes forward
        az_packet = LLPProtocol.create_packet(AZIMUTH_HEADER, AZIMUTH_FORWARD)
        el_packet = LLPProtocol.create_packet(ELEVATION_HEADER, ELEVATION_FORWARD)

        g5500.send_packet(az_packet)
        g5500.send_packet(el_packet)
        print("Both axes moving forward...")

        time.sleep(2)

        # Stop both axes
        az_stop = LLPProtocol.create_packet(AZIMUTH_HEADER, AZIMUTH_STOP)
        el_stop = LLPProtocol.create_packet(ELEVATION_HEADER, ELEVATION_STOP)

        g5500.send_packet(az_stop)
        g5500.send_packet(el_stop)
        print("Both axes stopped")

    print()


def example_show_packet():
    """Example: Display packet bytes without sending."""
    print("Example 3: Display packet bytes (dry-run)")
    print("-" * 50)

    # Create packets
    az_forward = LLPProtocol.create_packet(AZIMUTH_HEADER, AZIMUTH_FORWARD)
    el_stop = LLPProtocol.create_packet(ELEVATION_HEADER, ELEVATION_STOP)

    # Display as hex
    print(f"Azimuth Forward: {LLPProtocol.format_packet_hex(az_forward)}")
    print(f"Elevation Stop:  {LLPProtocol.format_packet_hex(el_stop)}")

    # Display command names
    print(f"\nCommand 1: {LLPProtocol.get_command_name(AZIMUTH_HEADER, AZIMUTH_FORWARD)}")
    print(f"Command 2: {LLPProtocol.get_command_name(ELEVATION_HEADER, ELEVATION_STOP)}")

    print()


def example_custom_sequence():
    """Example: Custom movement sequence."""
    print("Example 4: Custom sequence")
    print("-" * 50)

    sequence = [
        ("Azimuth Forward", AZIMUTH_HEADER, AZIMUTH_FORWARD, 2),
        ("Azimuth Stop", AZIMUTH_HEADER, AZIMUTH_STOP, 0.5),
        ("Elevation Forward", ELEVATION_HEADER, ELEVATION_FORWARD, 1.5),
        ("Elevation Stop", ELEVATION_HEADER, ELEVATION_STOP, 0.5),
    ]

    with G5500Serial() as g5500:
        print(f"Connected to {g5500.get_port()}")
        print()

        for name, header, command, duration in sequence:
            packet = LLPProtocol.create_packet(header, command)
            g5500.send_packet(packet)
            print(f"→ {name}")

            if duration > 0:
                time.sleep(duration)

        print("\nSequence completed!")

    print()


def example_interactive_mode():
    """Example: Using interactive mode programmatically."""
    print("Example 5: Interactive mode (programmatic)")
    print("-" * 50)
    print()
    print("To use interactive mode from Python:")
    print()
    print("from interactive_ui import InteractiveController")
    print("from serial_comm import G5500Serial")
    print("from protocol import *")
    print()
    print("def send_cmd(axis, command):")
    print("    # Your command sending logic")
    print("    pass")
    print()
    print("controller = InteractiveController(send_cmd)")
    print("controller.run()  # Blocks until user quits")
    print()
    print("Note: Interactive mode is best used via CLI:")
    print("  uv run g5500_cli.py interactive")
    print()


if __name__ == '__main__':
    print("G5500 CLI - Example Usage")
    print("=" * 50)
    print()

    # Run only the dry-run example by default
    # Uncomment other examples to run them (requires Arduino connected)
    example_show_packet()

    # Uncomment to run actual movement examples:
    # example_basic_movement()
    # example_both_axes()
    # example_custom_sequence()
    # example_interactive_mode()

    print("=" * 50)
    print("Examples completed!")
    print()
    print("TIP: For the easiest control experience, try:")
    print("  uv run g5500_cli.py interactive")
