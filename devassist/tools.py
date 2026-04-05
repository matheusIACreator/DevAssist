import datetime
import platform
import sys


def get_current_datetime() -> str:
    """Get the current date and time."""
    return datetime.datetime.now().isoformat()


def get_python_info() -> dict[str, str]:
    """Get information about the current Python environment."""
    return {
        "version": sys.version,
        "platform": platform.system(),
        "architecture": platform.architecture()[0],
    }


def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.

    Args:
        expression: A mathematical expression string, e.g. '2 + 2' or '10 * 5'
    """
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: invalid characters in expression"
    try:
        result = eval(expression, {"__builtins__": {}})  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error: {e}"