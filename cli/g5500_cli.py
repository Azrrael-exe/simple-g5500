#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.7"
# dependencies = [
#     "click>=8.1.0",
#     "pyserial>=3.5",
#     "readchar>=4.0.0",
# ]
# ///
"""
G5500 Controller CLI

Command-line interface for controlling the G5500 antenna rotator
via serial communication with Arduino.

Usage:
    uv run g5500_cli.py move --az forward --el stop
    uv run g5500_cli.py move --az forward --dry-run
    uv run g5500_cli.py ports
    uv run g5500_cli.py test
"""

import sys
import time
from typing import Optional, List, Tuple

import click

from protocol import (
    LLPProtocol,
    AZIMUTH_HEADER, ELEVATION_HEADER, FEEDBACK_HEADER,
    AZIMUTH_COMMANDS, ELEVATION_COMMANDS, FEEDBACK_COMMANDS
)
from serial_comm import G5500Serial, SerialConnectionError
from interactive_ui import InteractiveController, check_dependencies


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    G5500 Controller CLI - Control antenna rotator via serial connection.

    This tool allows you to control azimuth and elevation axes of the G5500
    antenna rotator controller. Commands are sent over serial using the LLP protocol.
    """
    pass


@cli.command()
@click.option('--az', '--azimuth', type=click.Choice(['forward', 'backward', 'stop']),
              help='Azimuth axis command')
@click.option('--el', '--elevation', type=click.Choice(['forward', 'backward', 'stop']),
              help='Elevation axis command')
@click.option('--port', '-p', type=str, default=None,
              help='Serial port (auto-detect if not specified)')
@click.option('--dry-run', is_flag=True,
              help='Show commands without sending them')
@click.option('--verbose', '-v', is_flag=True,
              help='Verbose output')
def move(az: Optional[str], el: Optional[str], port: Optional[str],
         dry_run: bool, verbose: bool):
    """
    Send movement commands to G5500 controller.

    You can control one or both axes in a single command.
    At least one axis command (--az or --el) must be specified.

    Examples:
        \b
        # Control single axis
        g5500_cli.py move --az forward
        g5500_cli.py move --el stop

        \b
        # Control both axes simultaneously
        g5500_cli.py move --az forward --el stop
        g5500_cli.py move --az backward --el forward

        \b
        # Dry run mode (show bytes without sending)
        g5500_cli.py move --az forward --dry-run

        \b
        # Specify port manually
        g5500_cli.py move --az forward --port /dev/ttyUSB0
    """
    # Validate that at least one axis is specified
    if az is None and el is None:
        click.echo(click.style("Error: At least one axis command (--az or --el) must be specified.", fg='red'))
        click.echo("\nUse --help for usage information.")
        sys.exit(1)

    # Build list of packets to send
    packets_to_send: List[Tuple[str, bytes]] = []

    if az:
        command = AZIMUTH_COMMANDS[az]
        packet = LLPProtocol.create_packet(AZIMUTH_HEADER, command)
        packets_to_send.append((f"Azimuth {az.capitalize()}", packet))

    if el:
        command = ELEVATION_COMMANDS[el]
        packet = LLPProtocol.create_packet(ELEVATION_HEADER, command)
        packets_to_send.append((f"Elevation {el.capitalize()}", packet))

    # Dry run mode: just display what would be sent
    if dry_run:
        click.echo(click.style("[DRY RUN]", fg='yellow', bold=True) +
                   f" Would send to port {port or 'auto-detect'}:")
        for name, packet in packets_to_send:
            hex_str = LLPProtocol.format_packet_hex(packet)
            click.echo(f"  {name:20s}: {hex_str}")
        return

    # Send commands over serial
    try:
        with G5500Serial(port=port) as g5500:
            actual_port = g5500.get_port()

            if verbose:
                click.echo(f"Connected to {actual_port}")

            for name, packet in packets_to_send:
                g5500.send_packet(packet)
                if verbose:
                    hex_str = LLPProtocol.format_packet_hex(packet)
                    click.echo(f"Sent {name}: {hex_str}")
                else:
                    click.echo(f"Sent: {name}")

            click.echo(click.style("✓ Commands sent successfully", fg='green'))

    except SerialConnectionError as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {e}", fg='red'))
        sys.exit(1)


@cli.command()
def ports():
    """
    List all available serial ports.

    This command displays all serial ports detected on the system,
    which is helpful when you need to manually specify a port.

    Example:
        g5500_cli.py ports
    """
    available_ports = G5500Serial.list_ports()

    if not available_ports:
        click.echo("No serial ports found.")
        return

    click.echo("Available serial ports:")
    click.echo()
    for port_path, port_desc in available_ports:
        click.echo(f"  {click.style(port_path, fg='cyan', bold=True)}")
        click.echo(f"    {port_desc}")
        click.echo()

    # Try to detect Arduino
    detected = G5500Serial.auto_detect_port()
    if detected:
        click.echo(click.style(f"Auto-detected Arduino at: {detected}", fg='green'))


@cli.command()
@click.option('--port', '-p', type=str, default=None,
              help='Serial port (auto-detect if not specified)')
@click.option('--dry-run', is_flag=True,
              help='Show test sequence without sending')
def test(port: Optional[str], dry_run: bool):
    """
    Run a test sequence to verify controller operation.

    This command sends a predefined sequence of movements to test
    both azimuth and elevation axes.

    Test sequence:
        1. Azimuth forward (2s)
        2. Azimuth stop
        3. Elevation forward (2s)
        4. Elevation stop
        5. Azimuth backward (2s)
        6. Azimuth stop
        7. Elevation backward (2s)
        8. Elevation stop

    Example:
        \b
        # Run test
        g5500_cli.py test

        \b
        # Preview test without running
        g5500_cli.py test --dry-run
    """
    # Define test sequence: (name, header, command, duration)
    sequence = [
        ("Azimuth Forward", AZIMUTH_HEADER, AZIMUTH_COMMANDS['forward'], 2.0),
        ("Azimuth Stop", AZIMUTH_HEADER, AZIMUTH_COMMANDS['stop'], 0.5),
        ("Elevation Forward", ELEVATION_HEADER, ELEVATION_COMMANDS['forward'], 2.0),
        ("Elevation Stop", ELEVATION_HEADER, ELEVATION_COMMANDS['stop'], 0.5),
        ("Azimuth Backward", AZIMUTH_HEADER, AZIMUTH_COMMANDS['backward'], 2.0),
        ("Azimuth Stop", AZIMUTH_HEADER, AZIMUTH_COMMANDS['stop'], 0.5),
        ("Elevation Backward", ELEVATION_HEADER, ELEVATION_COMMANDS['backward'], 2.0),
        ("Elevation Stop", ELEVATION_HEADER, ELEVATION_COMMANDS['stop'], 0.5),
    ]

    if dry_run:
        click.echo(click.style("[DRY RUN]", fg='yellow', bold=True) + " Test sequence:")
        click.echo()
        for i, (name, header, command, duration) in enumerate(sequence, 1):
            packet = LLPProtocol.create_packet(header, command)
            hex_str = LLPProtocol.format_packet_hex(packet)
            click.echo(f"{i}. {name:20s}: {hex_str} (wait {duration}s)")
        return

    click.echo("Starting test sequence...")
    click.echo("Press Ctrl+C to abort")
    click.echo()

    try:
        with G5500Serial(port=port) as g5500:
            actual_port = g5500.get_port()
            click.echo(f"Connected to {actual_port}")
            click.echo()

            for i, (name, header, command, duration) in enumerate(sequence, 1):
                packet = LLPProtocol.create_packet(header, command)
                g5500.send_packet(packet)

                click.echo(f"{i}/{len(sequence)}: {name}")

                if duration > 0:
                    time.sleep(duration)

            click.echo()
            click.echo(click.style("✓ Test sequence completed successfully", fg='green'))

    except SerialConnectionError as e:
        click.echo(click.style(f"\nError: {e}", fg='red'))
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\nTest interrupted by user")
        click.echo("Sending stop commands to both axes...")
        try:
            with G5500Serial(port=port) as g5500:
                # Emergency stop both axes
                stop_az = LLPProtocol.create_packet(AZIMUTH_HEADER, AZIMUTH_COMMANDS['stop'])
                stop_el = LLPProtocol.create_packet(ELEVATION_HEADER, ELEVATION_COMMANDS['stop'])
                g5500.send_packet(stop_az)
                g5500.send_packet(stop_el)
                click.echo(click.style("✓ Emergency stop sent", fg='yellow'))
        except:
            pass
        sys.exit(130)
    except Exception as e:
        click.echo(click.style(f"\nUnexpected error: {e}", fg='red'))
        sys.exit(1)


@cli.command()
@click.option('--port', '-p', type=str, default=None,
              help='Serial port (auto-detect if not specified)')
@click.option('--type', '-t', type=click.Choice(['voltage', 'angle', 'all']),
              default='voltage', help='Type of data to read')
@click.option('--verbose', '-v', is_flag=True,
              help='Verbose output')
def read(port: Optional[str], type: str, verbose: bool):
    """
    Read sensor feedback data from the controller.

    This command requests voltage and/or angle readings from
    the azimuth and elevation sensors.

    Examples:
        \b
        # Read voltages
        g5500_cli.py read
        g5500_cli.py read --type voltage

        \b
        # Read angles
        g5500_cli.py read --type angle

        \b
        # Read all data
        g5500_cli.py read --type all
    """
    try:
        with G5500Serial(port=port) as g5500:
            actual_port = g5500.get_port()

            if verbose:
                click.echo(f"Connected to {actual_port}")

            # Send read command
            command = FEEDBACK_COMMANDS[type]
            packet = LLPProtocol.create_packet(FEEDBACK_HEADER, command)

            # Flush input buffer to clear any residual data
            g5500.flush_input()

            g5500.send_packet(packet)

            if verbose:
                hex_str = LLPProtocol.format_packet_hex(packet)
                click.echo(f"Sent read command: {hex_str}")

            # Wait for response
            time.sleep(0.5)

            # Read response with debug enabled if verbose
            response = g5500.read_response(timeout=2.0, debug=verbose)

            if response:
                click.echo("Sensor readings:")
                az_v = response.get('az_voltage', 0) / 1000.0
                el_v = response.get('el_voltage', 0) / 1000.0
                click.echo(f"  Azimuth voltage:   {az_v:.3f} V")
                click.echo(f"  Elevation voltage: {el_v:.3f} V")

                if type == 'all' or type == 'angle':
                    az_a = response.get('az_angle', 0) / 10.0
                    el_a = response.get('el_angle', 0) / 10.0
                    click.echo(f"  Azimuth angle:     {az_a:.1f}°")
                    click.echo(f"  Elevation angle:   {el_a:.1f}°")
            else:
                click.echo(click.style("No response received", fg='yellow'))

    except SerialConnectionError as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {e}", fg='red'))
        sys.exit(1)


@cli.command()
@click.option('--port', '-p', type=str, default=None,
              help='Serial port (auto-detect if not specified)')
@click.option('--debug', '-d', is_flag=True,
              help='Enable debug output for sensor readings')
def interactive(port: Optional[str], debug: bool):
    """
    Interactive control mode using keyboard.

    Control the G5500 rotator interactively using your keyboard:
        - Arrow keys ←/→ control azimuth (left/right)
        - Arrow keys ↑/↓ control elevation (up/down)
        - SPACE bar stops all axes
        - Q or ESC to quit

    This mode provides real-time control with visual feedback including
    sensor readings (voltage and angle).

    Example:
        uv run g5500_cli.py interactive
    """
    # Check dependencies
    if not check_dependencies():
        click.echo(click.style("Error: Required dependencies not available", fg='red'))
        click.echo("\nFor better cross-platform support, install readchar:")
        click.echo("  pip install readchar")
        click.echo("\nOr update the script dependencies to include readchar.")
        sys.exit(1)

    try:
        # Connect to serial port
        g5500 = G5500Serial(port=port)
        g5500.connect()
        actual_port = g5500.get_port()

        click.echo(f"Connected to {actual_port}")
        click.echo("Starting interactive mode...\n")
        time.sleep(0.5)

        # Create command sender function
        def send_command(axis: str, command: str):
            """Send command to G5500."""
            try:
                if axis == 'azimuth':
                    header = AZIMUTH_HEADER
                    cmd = AZIMUTH_COMMANDS[command]
                else:  # elevation
                    header = ELEVATION_HEADER
                    cmd = ELEVATION_COMMANDS[command]

                packet = LLPProtocol.create_packet(header, cmd)
                g5500.send_packet(packet)
            except Exception as e:
                pass  # Silently ignore in interactive mode

        # Create feedback reader function
        def read_feedback():
            """Read feedback from G5500."""
            try:
                packet = LLPProtocol.create_packet(FEEDBACK_HEADER, FEEDBACK_COMMANDS['all'])
                g5500.flush_input()  # Clear buffer before sending
                g5500.send_packet(packet)
                time.sleep(0.1)  # Small delay for Arduino to respond
                return g5500.read_response(timeout=1.0, debug=debug)
            except Exception as e:
                print(f"\n[ERROR] Failed to read feedback: {e}")
                return None

        # Start interactive controller with both callbacks
        controller = InteractiveController(send_command, read_feedback)
        controller.run()

        # Cleanup
        g5500.disconnect()

    except SerialConnectionError as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user")
        try:
            if g5500.is_connected():
                # Emergency stop
                stop_az = LLPProtocol.create_packet(AZIMUTH_HEADER, AZIMUTH_COMMANDS['stop'])
                stop_el = LLPProtocol.create_packet(ELEVATION_HEADER, ELEVATION_COMMANDS['stop'])
                g5500.send_packet(stop_az)
                g5500.send_packet(stop_el)
                g5500.disconnect()
                click.echo(click.style("✓ Emergency stop sent", fg='yellow'))
        except:
            pass
        sys.exit(130)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {e}", fg='red'))
        try:
            if g5500 and g5500.is_connected():
                g5500.disconnect()
        except:
            pass
        sys.exit(1)


if __name__ == '__main__':
    cli()
