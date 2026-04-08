import datetime
import os
import platform
import sys


def get_current_datetime() -> str:
    return datetime.datetime.now().isoformat()


def get_python_info() -> dict[str, str]:
    return {
        "version": sys.version,
        "platform": platform.system(),
        "architecture": platform.architecture()[0],
    }


def calculate(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: invalid characters in expression"
    try:
        result = eval(expression, {"__builtins__": {}})  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def read_local_file(file_path: str) -> str:
    """
    Read the contents of a local file.
    
    Args:
        file_path: Absolute or relative path to the file.
    """
    try:
        path = os.path.expanduser(file_path)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            return f"Error: file is empty — {file_path}"
        # Limita a 3000 chars para não explodir o context
        if len(content) > 3000:
            return content[:3000] + "\n\n[... file truncated at 3000 chars ...]"
        return content
    except FileNotFoundError:
        return f"Error: file not found — {file_path}"
    except Exception as e:
        return f"Error reading file: {e}"