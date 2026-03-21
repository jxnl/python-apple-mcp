"""
AppleScript utility module for executing AppleScript commands from Python.

This module provides a consistent interface for executing AppleScript commands
and handling their results with comprehensive logging.
"""

import subprocess
import logging
import json
import time
import functools
import inspect
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, cast

# Configure logger
logger = logging.getLogger(__name__)

# Create a formatter for better log formatting
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Type variable for function return type
T = TypeVar('T')

def log_execution_time(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to log function execution time
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        func_name = func.__name__
        # Generate a unique ID for this call
        call_id = str(id(args[0]))[:8] if args else str(id(func))[:8]
        
        arg_info = []
        for i, arg in enumerate(args):
            if i == 0 and func_name in ["run_applescript", "run_applescript_async"]:
                # For AppleScript functions, truncate the first argument (script)
                truncated = str(arg)[:50] + ("..." if len(str(arg)) > 50 else "")
                arg_info.append(f"script={truncated}")
            else:
                arg_info.append(f"{type(arg).__name__}")
        
        for k, v in kwargs.items():
            arg_info.append(f"{k}={type(v).__name__}")
        
        args_str = ", ".join(arg_info)
        logger.debug(f"[{call_id}] Calling {func_name}({args_str})")
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log result summary based on type
            if func_name in ["run_applescript", "run_applescript_async"]:
                result_str = str(result)[:50] + ("..." if len(str(result)) > 50 else "")
                logger.debug(f"[{call_id}] {func_name} returned in {execution_time:.4f}s: {result_str}")
            else:
                result_type = type(result).__name__
                if isinstance(result, (list, dict)):
                    size = len(result)
                    logger.debug(f"[{call_id}] {func_name} returned {result_type}[{size}] in {execution_time:.4f}s")
                else:
                    logger.debug(f"[{call_id}] {func_name} returned {result_type} in {execution_time:.4f}s")
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"[{call_id}] {func_name} raised {type(e).__name__} after {execution_time:.4f}s: {str(e)}")
            raise
    
    return cast(Callable[..., T], wrapper)

class AppleScriptError(Exception):
    """Exception raised when an AppleScript execution fails"""
    pass

@log_execution_time
def run_applescript(script: str) -> str:
    """
    Execute an AppleScript command and return its output
    
    Args:
        script: The AppleScript command to execute
        
    Returns:
        The output of the AppleScript command as a string
        
    Raises:
        AppleScriptError: If the AppleScript command fails
    """
    truncated_script = script[:200] + ("..." if len(script) > 200 else "")
    logger.debug(f"Executing AppleScript: {truncated_script}")
    
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip()
        truncated_output = output[:200] + ("..." if len(output) > 200 else "")
        logger.debug(f"Output: {truncated_output}")
        
        return output
    except subprocess.CalledProcessError as e:
        error_msg = f"AppleScript error: {e.stderr.strip() if e.stderr else e}"
        logger.error(error_msg)
        raise AppleScriptError(error_msg)

async def run_applescript_async(script: str) -> str:
    """
    Execute an AppleScript command asynchronously
    
    Args:
        script: The AppleScript command to execute
        
    Returns:
        The output of the AppleScript command as a string
        
    Raises:
        AppleScriptError: If the AppleScript command fails
    """
    import asyncio
    
    # Custom logging for async function since decorator doesn't work with async functions
    call_id = str(id(script))[:8]
    truncated_script = script[:200] + ("..." if len(script) > 200 else "")
    logger.debug(f"[{call_id}] Calling run_applescript_async(script={truncated_script})")
    logger.debug(f"Executing AppleScript async: {truncated_script}")
    
    start_time = time.time()
    try:
        process = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        execution_time = time.time() - start_time
        
        if process.returncode != 0:
            error_msg = f"AppleScript error: {stderr.decode().strip()}"
            logger.error(error_msg)
            logger.error(f"[{call_id}] run_applescript_async raised AppleScriptError after {execution_time:.4f}s: {error_msg}")
            raise AppleScriptError(error_msg)
        
        output = stdout.decode().strip()
        truncated_output = output[:200] + ("..." if len(output) > 200 else "")
        
        logger.debug(f"Output: {truncated_output}")
        logger.debug(f"[{call_id}] run_applescript_async returned in {execution_time:.4f}s: {truncated_output}")
        
        return output
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Error executing AppleScript: {str(e)}"
        logger.error(error_msg)
        logger.error(f"[{call_id}] run_applescript_async raised {type(e).__name__} after {execution_time:.4f}s: {str(e)}")
        raise AppleScriptError(error_msg)

@log_execution_time
def parse_applescript_list(output: str) -> List[str]:
    """
    Parse an AppleScript list result into a Python list
    
    Args:
        output: The AppleScript output string containing a list
        
    Returns:
        A Python list of strings parsed from the AppleScript output
    """
    truncated_output = output[:50] + ("..." if len(output) > 50 else "")
    logger.debug(f"Parsing AppleScript list: {truncated_output}")
    
    if not output:
        logger.debug("Empty list input, returning empty list")
        return []
    
    # Remove leading/trailing braces if present
    output = output.strip()
    if output.startswith('{') and output.endswith('}'):
        output = output[1:-1]
        logger.debug("Removed braces from list")
    
    # Split by commas, handling quoted items correctly
    result = []
    current = ""
    in_quotes = False
    
    for char in output:
        if char == '"' and (not current or current[-1] != '\\'):
            in_quotes = not in_quotes
            current += char
        elif char == ',' and not in_quotes:
            result.append(current.strip())
            current = ""
        else:
            current += char
    
    if current:
        result.append(current.strip())
    
    # Clean up any quotes
    cleaned_result = []
    for item in result:
        item = item.strip()
        if item.startswith('"') and item.endswith('"'):
            item = item[1:-1]
        cleaned_result.append(item)
    
    logger.debug(f"Parsed list with {len(cleaned_result)} items")
    
    return cleaned_result

@log_execution_time
def parse_applescript_record(output: str) -> Dict[str, Any]:
    """
    Parse an AppleScript record into a Python dictionary
    
    Args:
        output: The AppleScript output string containing a record
        
    Returns:
        A Python dictionary parsed from the AppleScript record
    """
    truncated_output = output[:50] + ("..." if len(output) > 50 else "")
    logger.debug(f"Parsing AppleScript record: {truncated_output}")
    
    if not output:
        logger.debug("Empty record input, returning empty dictionary")
        return {}
    
    # Remove leading/trailing braces if present
    output = output.strip()
    if output.startswith('{') and output.endswith('}'):
        output = output[1:-1]
        logger.debug("Removed braces from record")
    
    # Parse key-value pairs
    result = {}
    current_key = None
    current_value = ""
    in_quotes = False
    i = 0
    
    while i < len(output):
        if output[i:i+2] == ':=' and not in_quotes and current_key is None:
            # Key definition
            current_key = current_value.strip()
            current_value = ""
            i += 2
            logger.debug(f"Found key: {current_key}")
        elif output[i] == ',' and not in_quotes and current_key is not None:
            # End of key-value pair
            parsed_value = parse_value(current_value.strip())
            result[current_key] = parsed_value
            logger.debug(f"Added key-value pair: {current_key}={type(parsed_value).__name__}")
            current_key = None
            current_value = ""
            i += 1
        elif output[i] == '"' and (not current_value or current_value[-1] != '\\'):
            # Toggle quote state
            in_quotes = not in_quotes
            current_value += output[i]
            i += 1
        else:
            current_value += output[i]
            i += 1
    
    # Add the last key-value pair
    if current_key is not None:
        parsed_value = parse_value(current_value.strip())
        result[current_key] = parsed_value
        logger.debug(f"Added final key-value pair: {current_key}={type(parsed_value).__name__}")
    
    logger.debug(f"Parsed record with {len(result)} key-value pairs")
    
    return result

def parse_value(value: str) -> Any:
    """
    Parse a value from AppleScript output into an appropriate Python type
    
    Args:
        value: The string value to parse
        
    Returns:
        The parsed value as an appropriate Python type
    """
    original_value = value
    value = value.strip()
    
    # Handle quoted strings
    if value.startswith('"') and value.endswith('"'):
        result = value[1:-1]
        logger.debug(f"Parsed quoted string: '{result}'")
        return result
    
    # Handle numbers
    try:
        if '.' in value:
            result = float(value)
            logger.debug(f"Parsed float: {result}")
            return result
        result = int(value)
        logger.debug(f"Parsed integer: {result}")
        return result
    except ValueError:
        # Not a number, continue with other types
        pass
    
    # Handle booleans
    if value.lower() == 'true':
        logger.debug("Parsed boolean: True")
        return True
    if value.lower() == 'false':
        logger.debug("Parsed boolean: False")
        return False
    
    # Handle missing values
    if value.lower() == 'missing value':
        logger.debug("Parsed missing value as None")
        return None
    
    # Handle lists
    if value.startswith('{') and value.endswith('}'):
        result = parse_applescript_list(value)
        logger.debug(f"Parsed nested list with {len(result)} items")
        return result
    
    # Return as string by default
    logger.debug(f"No specific type detected, returning as string: '{value}'")
    return value

# Maximum input length (100KB) to prevent denial-of-service via oversized strings
MAX_INPUT_LENGTH = 102400

def escape_string(s: str) -> str:
    """
    Escape special characters in a string for use in AppleScript.

    This prevents AppleScript injection by neutralising characters that
    could break out of a quoted string context.  Inputs longer than
    MAX_INPUT_LENGTH are truncated before escaping to guard against
    denial-of-service attacks.

    Args:
        s: The string to escape

    Returns:
        The escaped string safe for interpolation inside AppleScript double-quotes
    """
    # Remove null bytes and neutralise newlines to prevent statement injection
    s = s.replace('\x00', '')
    s = s.replace('\n', ' ').replace('\r', ' ')
    encoded = s.encode('utf-8')
    if len(encoded) > MAX_INPUT_LENGTH:
        logger.warning(
            f"Input string truncated from {len(encoded)} to {MAX_INPUT_LENGTH} bytes"
        )
        s = encoded[:MAX_INPUT_LENGTH].decode('utf-8', errors='ignore')
    return s.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")

def format_applescript_value(value: Any) -> str:
    """
    Format a Python value for use in AppleScript
    
    Args:
        value: The Python value to format
        
    Returns:
        The formatted value as a string for use in AppleScript
    """
    logger.debug(f"Formatting Python value of type {type(value).__name__} for AppleScript")
    
    if value is None:
        logger.debug("Formatting None as 'missing value'")
        return "missing value"
    elif isinstance(value, bool):
        result = str(value).lower()
        logger.debug(f"Formatting boolean as '{result}'")
        return result
    elif isinstance(value, (int, float)):
        result = str(value)
        logger.debug(f"Formatting number as '{result}'")
        return result
    elif isinstance(value, list):
        logger.debug(f"Formatting list with {len(value)} items")
        items = [format_applescript_value(item) for item in value]
        return "{" + ", ".join(items) + "}"
    elif isinstance(value, dict):
        logger.debug(f"Formatting dictionary with {len(value)} key-value pairs")
        pairs = [f"{k}:{format_applescript_value(v)}" for k, v in value.items()]
        return "{" + ", ".join(pairs) + "}"
    else:
        result = f'"{escape_string(str(value))}"'
        logger.debug(f"Formatting string as {result}")
        return result


def configure_logging(level=logging.INFO, add_file_handler=False, log_file=None):
    """
    Configure logging for the AppleScript module
    
    Args:
        level: The logging level to use (default: INFO)
        add_file_handler: Whether to add a file handler (default: False)
        log_file: Path to the log file (default: applescript.log in current directory)
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler
    logger.addHandler(console_handler)
    
    # Add file handler if requested
    if add_file_handler:
        if log_file is None:
            log_file = "applescript.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.debug(f"Logging to file: {log_file}")
    
    logger.debug("AppleScript logging configured")