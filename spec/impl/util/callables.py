import inspect
from typing import Callable


def can_be_called_with_one_argument(c: Callable) -> bool:
    argspec = inspect.getfullargspec(c)
    default_arg_count = len(argspec.defaults) if argspec.defaults else 0
    non_default_arg_count = len(argspec.args) - default_arg_count

    if not (inspect.isbuiltin(c) or inspect.isfunction(c)):
        # this is a class with a __call__ method
        non_default_arg_count -= 1

    return non_default_arg_count == 1 \
           or (non_default_arg_count == 0 and argspec.varargs) \
           or default_arg_count >= 1