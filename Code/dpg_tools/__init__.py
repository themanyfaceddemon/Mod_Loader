from .center_win import center_window
from .decode import decode_string
from .timer import Timer


def add_timer(interval, callback, repeat_count=None, *args, **kwargs) -> Timer:
    return Timer(interval, callback, repeat_count, *args, **kwargs)
