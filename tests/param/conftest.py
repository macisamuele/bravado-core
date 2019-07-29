# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import pytest

from bravado_core.spec import Spec


@pytest.fixture
def empty_swagger_spec():
    return Spec(spec_dict={})
