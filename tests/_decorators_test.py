# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

from functools import partial

import pytest

from bravado_core._decorators import handle_null_value
from bravado_core._decorators import wrap_recursive_call_exception
from bravado_core.exception import SwaggerMappingError
from bravado_core.util import memoize_by_id


@pytest.mark.parametrize(
    'object_schema, value, expected_value',
    [
        ({'type': 'integer'}, 1, 1),
        ({'type': 'integer', 'default': 42}, 1, 1),
        ({'type': 'integer', 'default': 42}, None, 42),
        ({'type': 'integer', 'x-nullable': True}, 1, 1),
        ({'type': 'integer', 'x-nullable': True}, None, None),
        ({'type': 'integer', 'default': 42, 'x-nullable': True}, None, 42),
    ],
)
def test_handle_null_value(minimal_swagger_spec, object_schema, value, expected_value):
    @handle_null_value(minimal_swagger_spec, object_schema)
    def foo(param1):
        return param1

    assert foo(value) == expected_value


@pytest.mark.parametrize(
    'object_schema, value',
    [
        ({'type': 'integer'}, None),
    ],
)
def test_handle_null_value_raises(minimal_swagger_spec, object_schema, value):
    @handle_null_value(minimal_swagger_spec, object_schema)
    def foo(param1):
        return param1

    with pytest.raises(SwaggerMappingError):
        foo(value)


def test_wrap_recursive_call_exception_for_non_recursive_functions():
    def multiplier(param, value):
        return param * value

    @wrap_recursive_call_exception
    @memoize_by_id
    def foo(param):
        return partial(multiplier, param)

    func = foo(2)
    assert func.func == multiplier
    assert func.args == (2,)
    assert not func.keywords

    assert func(3) == 6


def test_wrap_recursive_call_exception_for_recursive_functions():
    # TODO: Update this test a bit to make it more realistic to the case
    #       of recursive specs (that was the reason why the decorator was
    #       created in the first place)

    class ControlledException(Exception):
        pass

    def _raise():
        raise ControlledException()

    @wrap_recursive_call_exception
    @memoize_by_id
    def foo():
        return foo()

    func = foo()
    assert func.__name__ == (lambda: 42).__name__

    # Manually modify the cached value of foo() assuming that a defined function is retrieved
    foo.cache[()] = _raise

    with pytest.raises(ControlledException):
        func()
