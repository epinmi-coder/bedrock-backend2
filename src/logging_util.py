import functools
from logger import logging
import time
import contextvars

tools_called = contextvars.ContextVar("tools_called", default=None)

def log_tool_call(tool_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Initialize the list if not already set
            tool_list = tools_called.get()
            if tool_list is None:
                tool_list = []
                tools_called.set(tool_list)
            tool_list.append(tool_name)
            start = time.time()
            logging.info(
                f"[TOOL CALL] Tool '{tool_name}' called with args={args}, kwargs={kwargs}"
            )
            try:
                result = func(*args, **kwargs)
                logging.info(
                    f"[TOOL CALL] Tool '{tool_name}' completed in {time.time()-start:.2f}s"
                )
                return result
            except Exception as e:
                logging.error(f"[TOOL CALL] Tool '{tool_name}' failed: {e}")
                raise

        return wrapper

    return decorator

def get_tools_called():
    """Returns the list of tools called in the current context, or an empty list."""
    tool_list = tools_called.get()
    return tool_list if tool_list is not None else []

def reset_tools_called():
    """Resets the tools_called context variable."""
    tools_called.set([])
