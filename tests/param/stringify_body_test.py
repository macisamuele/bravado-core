# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import json

from bravado_core.param import stringify_body


def test_stringify_body_converts_dict_to_str():
    body = {'foo': 'bar', 'bar': 42}
    body_str = stringify_body(body)
    assert body == json.loads(body_str)


def test_stringify_body_ignores_data_if_already_str():
    assert 'foo' == stringify_body('foo')
