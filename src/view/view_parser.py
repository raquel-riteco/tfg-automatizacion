ESC             = "\x1b"
RESET_ALL       = f"{ESC}[0m"
ERROR           = f"{ESC}[38;5;196m"  # Red
WARNING         = f"{ESC}[38;5;208m"  # Orange
NOT_AVAILABLE   = f"{ESC}[38;5;245m"  # Grey
OK              = f"{ESC}[92m"        # Green
DEBUG           = f"{ESC}[38;5;39m"   # Blue


def parse_error(msg: str) -> str:
    """
    Formats the given error message in red color.

    Args:
        msg (str): The error message to be formatted.

    Returns:
        str: The formatted error message in red.
    """
    return f"{ERROR}ERROR: {msg}{RESET_ALL}"


def parse_warning(msg: str) -> str:
    """
    Formats the given warning message in orange color.

    Args:
        msg (str): The warning message to be formatted.

    Returns:
        str: The formatted warning message in orange.
    """
    return f"{WARNING}WARNING: {msg}{RESET_ALL}"


def parse_not_available(msg: str) -> str:
    """
    Formats the given message indicating unavailability in grey color.

    Args:
        msg (str): The message indicating unavailability.

    Returns:
        str: The formatted unavailability message in grey.
    """
    return f"{NOT_AVAILABLE}{msg}{RESET_ALL}"


def parse_ok(msg: str) -> str:
    """
    Formats the given success message in green color.

    Args:
        msg (str): The success message to be formatted.

    Returns:
        str: The formatted success message in green.
    """
    return f"{OK}{msg}{RESET_ALL}"


def parse_debug(msg: str) -> str:
    """
    Formats the given debug message in blue color.

    Args:
        msg (str): The debug message to be formatted.

    Returns:
        str: The formatted debug message in blue.
    """
    return f"{DEBUG}DEBUG: {msg}{RESET_ALL}"

