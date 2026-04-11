"""
Interactive UI module for G5500 Controller.

Provides a console-based interactive interface for controlling the antenna
rotator using keyboard arrow keys and spacebar.
"""

import sys
import threading
import time
from enum import Enum
from typing import Callable, Optional

try:
    # Try to import readchar (works better cross-platform)
    import readchar

    HAS_READCHAR = True
except ImportError:
    HAS_READCHAR = False
    # Fallback to platform-specific implementations
    if sys.platform == "win32":
        import msvcrt
    else:
        import termios
        import tty


class KeyCode:
    """Key codes for cross-platform keyboard input."""

    # Arrow keys
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    # Control keys
    SPACE = "space"
    ESC = "esc"
    Q = "q"
    R = "r"

    # Platform-specific codes
    if sys.platform != "win32":
        # Unix/Linux/macOS arrow key sequences
        ARROW_UP = "\x1b[A"
        ARROW_DOWN = "\x1b[B"
        ARROW_RIGHT = "\x1b[C"
        ARROW_LEFT = "\x1b[D"
    else:
        # Windows arrow key codes
        ARROW_UP = b"H"
        ARROW_DOWN = b"P"
        ARROW_RIGHT = b"M"
        ARROW_LEFT = b"K"


class AxisState(Enum):
    """Axis movement state."""

    STOPPED = 0
    FORWARD = 1
    BACKWARD = 2


class InteractiveController:
    """
    Interactive console controller for G5500.

    Controls:
        ↑/↓     - Elevation up/down
        ←/→     - Azimuth left/right
        SPACE   - Stop all axes
        R       - Read sensor values
        Q/ESC   - Quit
    """

    def __init__(self, send_command_callback: Callable, read_feedback_callback: Optional[Callable] = None):
        """
        Initialize interactive controller.

        Args:
            send_command_callback: Function to call to send commands.
                                 Should accept (axis, command) parameters.
            read_feedback_callback: Optional function to read feedback data.
                                  Should return dict with sensor readings.
        """
        self.send_command = send_command_callback
        self.read_feedback = read_feedback_callback
        self.azimuth_state = AxisState.STOPPED
        self.elevation_state = AxisState.STOPPED
        self.running = False
        self.status_lock = threading.Lock()

        # Sensor readings
        self.az_voltage = 0.0
        self.el_voltage = 0.0
        self.az_angle = 0.0
        self.el_angle = 0.0
        self.last_reading_time = 0
        self.readings_available = False

    def _get_key(self) -> Optional[str]:
        """
        Get a key press in a cross-platform way.

        Returns:
            Key string or None
        """
        if HAS_READCHAR:
            try:
                key = readchar.readkey()
                # Map readchar keys to our key codes
                if key == readchar.key.UP:
                    return KeyCode.UP
                elif key == readchar.key.DOWN:
                    return KeyCode.DOWN
                elif key == readchar.key.LEFT:
                    return KeyCode.LEFT
                elif key == readchar.key.RIGHT:
                    return KeyCode.RIGHT
                elif key == " ":
                    return KeyCode.SPACE
                elif key in ("\x1b", "\x03"):  # ESC or Ctrl+C
                    return KeyCode.ESC
                elif key.lower() == "q":
                    return KeyCode.Q
                elif key.lower() == "r":
                    return KeyCode.R
                return key
            except Exception:
                return None

        # Platform-specific fallback
        if sys.platform == "win32":
            return self._get_key_windows()
        else:
            return self._get_key_unix()

    def _get_key_windows(self) -> Optional[str]:
        """Get key press on Windows."""
        if msvcrt.kbhit():
            key = msvcrt.getch()

            if key == b"\xe0":  # Arrow key prefix
                key = msvcrt.getch()
                if key == KeyCode.ARROW_UP:
                    return KeyCode.UP
                elif key == KeyCode.ARROW_DOWN:
                    return KeyCode.DOWN
                elif key == KeyCode.ARROW_LEFT:
                    return KeyCode.LEFT
                elif key == KeyCode.ARROW_RIGHT:
                    return KeyCode.RIGHT
            elif key == b" ":
                return KeyCode.SPACE
            elif key == b"\x1b":  # ESC
                return KeyCode.ESC
            elif key.lower() == b"q":
                return KeyCode.Q
            elif key.lower() == b"r":
                return KeyCode.R
        return None

    def _get_key_unix(self) -> Optional[str]:
        """Get key press on Unix/Linux/macOS."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)

            # Check for escape sequences (arrow keys)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    if ch3 == "A":
                        return KeyCode.UP
                    elif ch3 == "B":
                        return KeyCode.DOWN
                    elif ch3 == "C":
                        return KeyCode.RIGHT
                    elif ch3 == "D":
                        return KeyCode.LEFT
                return KeyCode.ESC
            elif ch == " ":
                return KeyCode.SPACE
            elif ch.lower() == "q":
                return KeyCode.Q
            elif ch.lower() == "r":
                return KeyCode.R
            elif ch == "\x03":  # Ctrl+C
                return KeyCode.ESC

            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _update_azimuth(self, state: AxisState):
        """Update azimuth state and send command."""
        with self.status_lock:
            if self.azimuth_state != state:
                self.azimuth_state = state

                if state == AxisState.FORWARD:
                    self.send_command("azimuth", "forward")
                elif state == AxisState.BACKWARD:
                    self.send_command("azimuth", "backward")
                else:
                    self.send_command("azimuth", "stop")

    def _update_elevation(self, state: AxisState):
        """Update elevation state and send command."""
        with self.status_lock:
            if self.elevation_state != state:
                self.elevation_state = state

                if state == AxisState.FORWARD:
                    self.send_command("elevation", "forward")
                elif state == AxisState.BACKWARD:
                    self.send_command("elevation", "backward")
                else:
                    self.send_command("elevation", "stop")

    def _stop_all(self):
        """Stop both axes."""
        self._update_azimuth(AxisState.STOPPED)
        self._update_elevation(AxisState.STOPPED)

    def _update_readings(self):
        """Update sensor readings on demand (when R key is pressed)."""
        if self.read_feedback:
            try:
                print("\n[INFO] Reading sensors...", end="", flush=True)
                readings = self.read_feedback()
                if readings:
                    with self.status_lock:
                        self.az_voltage = readings.get('az_voltage', 0.0) / 1000.0  # mV to V
                        self.el_voltage = readings.get('el_voltage', 0.0) / 1000.0
                        self.az_angle = readings.get('az_angle', 0.0) / 10.0  # 0.1° to °
                        self.el_angle = readings.get('el_angle', 0.0) / 10.0
                        self.last_reading_time = time.time()
                        self.readings_available = True
                    print(" OK!")
                    return True
                else:
                    print(" No response received")
                    return False
            except Exception as e:
                print(f" ERROR: {e}")
                return False
        return False

    def _print_status(self):
        """Print current status with sensor readings."""
        az_status = {
            AxisState.STOPPED: "■ STOPPED",
            AxisState.FORWARD: "→ RIGHT   ",
            AxisState.BACKWARD: "← LEFT    ",
        }

        el_status = {
            AxisState.STOPPED: "■ STOPPED",
            AxisState.FORWARD: "↑ UP     ",
            AxisState.BACKWARD: "↓ DOWN   ",
        }

        # Clear line and print status
        sys.stdout.write("\r" + " " * 120 + "\r")

        if self.readings_available:
            status_line = (
                f"Az: {az_status[self.azimuth_state]} ({self.az_voltage:.2f}V, {self.az_angle:.1f}°) | "
                f"El: {el_status[self.elevation_state]} ({self.el_voltage:.2f}V, {self.el_angle:.1f}°)"
            )
        else:
            status_line = (
                f"Az: {az_status[self.azimuth_state]} | "
                f"El: {el_status[self.elevation_state]} | Press R to read sensors"
            )

        sys.stdout.write(status_line)
        sys.stdout.flush()

    def run(self):
        """
        Run the interactive controller.

        This will block until the user quits.
        """
        self.running = True

        # Print instructions
        print("=" * 60)
        print("G5500 Interactive Controller")
        print("=" * 60)
        print()
        print("Controls:")
        print("  ← / →       Azimuth Left/Right")
        print("  ↑ / ↓       Elevation Up/Down")
        print("  SPACE       Stop All Axes")
        print("  R           Read Sensor Values")
        print("  Q or ESC    Quit")
        print()
        print("=" * 60)
        print()
        print("Status: ", end="")
        sys.stdout.flush()

        try:
            while self.running:
                key = self._get_key()

                if key == KeyCode.UP:
                    self._update_elevation(AxisState.FORWARD)
                    self._print_status()

                elif key == KeyCode.DOWN:
                    self._update_elevation(AxisState.BACKWARD)
                    self._print_status()

                elif key == KeyCode.LEFT:
                    self._update_azimuth(AxisState.BACKWARD)
                    self._print_status()

                elif key == KeyCode.RIGHT:
                    self._update_azimuth(AxisState.FORWARD)
                    self._print_status()

                elif key == KeyCode.SPACE:
                    self._stop_all()
                    self._print_status()

                elif key == KeyCode.R:
                    # Read sensors on demand
                    if self._update_readings():
                        self._print_status()

                elif key in (KeyCode.Q, KeyCode.ESC):
                    break

                # Update display if no key was pressed
                if key is None:
                    self._print_status()

                # Small delay to prevent CPU spinning
                time.sleep(0.05)

        except KeyboardInterrupt:
            pass

        finally:
            # Stop all axes on exit
            print("\n\nStopping all axes...")
            self._stop_all()
            print("Exiting interactive mode.")
            self.running = False


def check_dependencies() -> bool:
    """
    Check if required dependencies are available.

    Returns:
        True if dependencies are met, False otherwise
    """
    if HAS_READCHAR:
        return True

    # Check platform-specific requirements
    if sys.platform == "win32":
        try:
            import msvcrt

            return True
        except ImportError:
            return False
    else:
        try:
            import termios
            import tty

            return True
        except ImportError:
            return False
