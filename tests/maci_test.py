# -*- coding: utf-8 -*-
import json
import os

import pytest

from bravado_core.spec import Spec


@pytest.fixture
def spec_spec(my_dir):
    spec_path = os.path.join(my_dir, '../test-data/2.0/polymorphic_models_referenced_by_polymorphic_models/swagger.json')
    with open(spec_path) as f:
        spec_dict = json.load(f)

    yield Spec.from_dict(
        spec_dict,
        origin_url='file://{}'.format(spec_path),
        config={
            'validate_swagger_spec': False,
            'internally_dereference_refs': True,
        },
    )


def test_fafa(spec_spec):
    assert 'Content1' in spec_spec.definitions
