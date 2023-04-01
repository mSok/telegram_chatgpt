import ast
import os

import src.log_tools

from .base import *

# Override config variables from environment
# To override config variable with given name, set environment variable to `_module_prefix` + that name


_MODULE_PREFIX = "BOT_"
for key, value in os.environ.items():
    if not key.startswith(_MODULE_PREFIX):
        continue
    pure_key = key[len(_MODULE_PREFIX) :]
    if pure_key not in locals():
        continue

    try:
        locals()[pure_key] = ast.literal_eval(value)
    except:  # pylint: disable=bare-except
        locals()[pure_key] = value
