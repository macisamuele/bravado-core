# -*- coding: utf-8 -*-
import six

if six.PY2:
    from functools32 import wraps  # noqa: F401
else:
    from functools import wraps  # noqa: F401
