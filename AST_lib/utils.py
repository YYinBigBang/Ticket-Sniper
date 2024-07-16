import os
import sys
import time
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import wraps, partial

# Create a global ThreadPoolExecutor instance
executor = ThreadPoolExecutor(max_workers=10)


def get_logger():
    """Set logging and return an instance of logger."""
    _logger = logging.getLogger()
    _logger.setLevel(logging.DEBUG)
    stdout_handler = logging.StreamHandler(sys.stdout)
    _logger.addHandler(stdout_handler)
    # writing the log to the file.
    curr_date = time.strftime("%m%d")
    log_path = './Logger'
    log_name = f'AST_log_{curr_date}.log'
    log_file = f'{log_path}/{log_name}'
    os.makedirs(log_path, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)
    return _logger


def timelog(func):
    """Decorator for recording function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            print(f'[Phase: {func.__name__}] ------------- START')
            return func(*args, **kwargs)
        finally:
            elapsed_time = time.time() - start_time
            print(f"[Phase: {func.__name__}] ------------- END in {elapsed_time:.3f}(s)")
    return wrapper


def asyncify(sync_func):
    """Decorator to make a synchronous function callable in an async context."""
    @wraps(sync_func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        # Create a partial function that includes both args and kwargs
        func = partial(sync_func, *args, **kwargs)
        return await loop.run_in_executor(None, func)
    return wrapper


def syncify(async_func):
    """Decorator to make an async function callable from a sync context."""
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        try:
            # Check if there's an existing running event loop
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If the loop is running, use run_coroutine_threadsafe to avoid blocking the loop
            future = asyncio.run_coroutine_threadsafe(async_func(*args, **kwargs), loop)
            return future.result()
        else:
            return asyncio.run(async_func(*args, **kwargs))
    return wrapper


def fork_thread(func):
    """Decorator for launching parallel tasks."""
    @wraps(func)
    def wrapper(*wrap_args, **wrap_kwargs):
        def run_func(*func_args, **func_kwargs):
            try:
                print(f'Thread fork[{func.__name__}] start')
                return func(*func_args, **func_kwargs)
            except Exception as e:
                print(f"Thread exception in function [{func.__name__}]: {e}")
        return executor.submit(run_func, *wrap_args, **wrap_kwargs)
    return wrapper


#####################################################################################################
# TODO: A feature for printing a tabular data on log.
"""
def print_tabular_data(header=None, align='^', padding=15, *elements: list) -> None:
    fmt_align = f'{align}{padding}'
    fmt_line = '+' + f'-{"-" * padding}-+' * (len(elements))

    if header:
        fmt_header_line = '+' + f'-{"-" * padding}-+' * (len(header))
        fmt_header = '|'
        for title in header:
            fmt_header += f' {title:{fmt_align}} |'
        print(fmt_header_line)
        print(fmt_header)
        print(fmt_header_line)
    else:
        print(fmt_line)

    for row in zip(*elements):
        fmt_row_label = '|' + ' {:{fmt_align}} |' * len(elements)
        fmt_row = fmt_row_label.format(*row)
        print(fmt_row)

    print(fmt_line)  # Print the bottom line of the table
"""
