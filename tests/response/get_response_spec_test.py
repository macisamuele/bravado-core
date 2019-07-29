# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import pytest

from bravado_core.exception import MatchingResponseNotFound
from bravado_core.operation import Operation
from bravado_core.response import get_response_spec


@pytest.fixture
def op_spec():
    return {
        'responses': {
            '200': {
                'description': 'Get pet by id',
            },
            'default': {
                'description': 'Uh, I guess everything is OK',
            },
        },
    }


def test_return_spec_for_status_code(empty_swagger_spec, op_spec):
    op = Operation(empty_swagger_spec, '/pet/{petId}', 'get', op_spec)
    assert op_spec['responses']['200'] == get_response_spec(200, op)


def test_return_default_spec_when_no_match_on_status_code(empty_swagger_spec, op_spec):
    op = Operation(empty_swagger_spec, '/pet/{petId}', 'get', op_spec)
    assert op_spec['responses']['default'] == get_response_spec(404, op)


def test_raise_error_when_no_default_and_no_status_code_match(empty_swagger_spec, op_spec):
    del op_spec['responses']['default']
    op = Operation(empty_swagger_spec, '/pet/{petId}', 'get', op_spec)
    with pytest.raises(MatchingResponseNotFound) as excinfo:
        get_response_spec(404, op)
    assert 'not found' in str(excinfo.value)
