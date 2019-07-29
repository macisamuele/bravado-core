# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import msgpack
import pytest
from jsonschema import ValidationError
from mock import Mock
from mock import patch

from bravado_core.content_type import APP_JSON
from bravado_core.content_type import APP_MSGPACK
from bravado_core.response import IncomingResponse
from bravado_core.response import unmarshal_response


@pytest.fixture
def response_spec():
    return {
        'description': "Day of the week",
        'schema': {
            'type': 'string',
        },
    }


def test_no_content(empty_swagger_spec):
    response_spec = {
        'description': "I don't have a 'schema' key so I return nothing",
    }
    response = Mock(spec=IncomingResponse, status_code=200)

    with patch('bravado_core.response.get_response_spec') as m:
        m.return_value = response_spec
        op = Mock(swagger_spec=empty_swagger_spec)
        result = unmarshal_response(response, op)
        assert result is None


def test_json_content(empty_swagger_spec, response_spec):
    response = Mock(
        spec=IncomingResponse,
        status_code=200,
        headers={'content-type': APP_JSON},
        json=Mock(return_value='Monday'),
    )

    with patch('bravado_core.response.get_response_spec') as m:
        m.return_value = response_spec
        op = Mock(swagger_spec=empty_swagger_spec)
        assert 'Monday' == unmarshal_response(response, op)


def test_msgpack_content(empty_swagger_spec, response_spec):
    message = 'Monday'
    response = Mock(
        spec=IncomingResponse,
        status_code=200,
        headers={'content-type': APP_MSGPACK},
        raw_bytes=msgpack.dumps(message, use_bin_type=True),
    )

    with patch(
        'bravado_core.response.get_response_spec',
        return_value=response_spec,
    ):
        op = Mock(swagger_spec=empty_swagger_spec)
        assert message == unmarshal_response(response, op)


def test_text_content(empty_swagger_spec, response_spec):
    response = Mock(
        spec=IncomingResponse,
        status_code=200,
        headers={'content-type': 'text/plain'},
        text='Monday',
    )

    with patch('bravado_core.response.get_response_spec') as m:
        m.return_value = response_spec
        op = Mock(swagger_spec=empty_swagger_spec)
        assert 'Monday' == unmarshal_response(response, op)


def test_skips_validation(empty_swagger_spec, response_spec):
    empty_swagger_spec.config['validate_responses'] = False
    response = Mock(
        spec=IncomingResponse,
        status_code=200,
        headers={'content-type': APP_JSON},
        json=Mock(return_value='Monday'),
    )

    with patch('bravado_core.response.validate_schema_object') as val_schem:
        with patch('bravado_core.response.get_response_spec') as get_resp:
            get_resp.return_value = response_spec
            op = Mock(swagger_spec=empty_swagger_spec)
            unmarshal_response(response, op)
            assert val_schem.call_count == 0


def test_performs_validation(empty_swagger_spec, response_spec):
    empty_swagger_spec.config['validate_responses'] = True
    response = Mock(
        spec=IncomingResponse,
        status_code=200,
        headers={'content-type': APP_JSON},
        json=Mock(return_value='Monday'),
    )

    with patch('bravado_core.response.validate_schema_object') as val_schem:
        with patch('bravado_core.response.get_response_spec') as get_resp:
            get_resp.return_value = response_spec
            op = Mock(swagger_spec=empty_swagger_spec)
            unmarshal_response(response, op)
            assert val_schem.call_count == 1


def test_unmarshal_model_polymorphic_specs(polymorphic_spec):
    pet_list_dicts = [
        {
            'name': 'a dog name',
            'type': 'Dog',
            'birth_date': '2017-03-09',
        },
        {
            'name': 'a cat name',
            'type': 'Cat',
            'color': 'white',
        },
    ]
    pet_list_models = unmarshal_response(
        response=Mock(
            spec=IncomingResponse,
            status_code=200,
            headers={'content-type': APP_JSON},
            json=Mock(return_value=pet_list_dicts),
        ),
        op=polymorphic_spec.resources['pets'].operations['get_pets'],
    )

    assert len(pet_list_dicts) == len(pet_list_models)

    for list_item_model, list_item_dict in zip(pet_list_models, pet_list_dicts):
        assert isinstance(list_item_model, polymorphic_spec.definitions['GenericPet'])
        assert isinstance(list_item_model, polymorphic_spec.definitions[list_item_dict['type']])
        assert list_item_model._marshal() == list_item_dict


def test_unmarshal_model_polymorphic_specs_with_invalid_discriminator(polymorphic_spec):
    pet_list_dicts = [
        {
            'name': 'a dog name',
            'type': 'a-random-value',
            'birth_date': '2017-03-09',
        },
    ]
    with pytest.raises(ValidationError):
        # Expecting validation error as "a-random-value" is not a valid type
        unmarshal_response(
            response=Mock(
                spec=IncomingResponse,
                status_code=200,
                headers={'content-type': APP_JSON},
                json=Mock(return_value=pet_list_dicts),
            ),
            op=polymorphic_spec.resources['pets'].operations['get_pets'],
        )
