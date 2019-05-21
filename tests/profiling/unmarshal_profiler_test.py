# -*- coding: utf-8 -*-
import pytest
from jsonpointer import JsonPointer

from bravado_core.unmarshal import unmarshal_schema_object


@pytest.fixture
def findByStatusReponseSchema(perf_petstore_spec):
    return perf_petstore_spec._force_deref(
        {
            '$ref': '#{}'.format(
                JsonPointer.from_parts(
                    ['paths', '/pet/findByStatus', 'get', 'responses', '200', 'schema'],
                ).path,
            ),
        },
    )


def test_small_objects(benchmark, perf_petstore_spec, findByStatusReponseSchema, small_pets):
    benchmark(
        unmarshal_schema_object,
        perf_petstore_spec,
        findByStatusReponseSchema,
        small_pets,
    )


def test_large_objects(benchmark, perf_petstore_spec, findByStatusReponseSchema, large_pets):
    benchmark(
        unmarshal_schema_object,
        perf_petstore_spec,
        findByStatusReponseSchema,
        large_pets,
    )
