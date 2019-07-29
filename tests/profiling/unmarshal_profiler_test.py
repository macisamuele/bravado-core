# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

from bravado_core.unmarshal import unmarshal_schema_object


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
