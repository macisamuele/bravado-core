# -*- coding: utf-8 -*-
from functools import partial

from six import iteritems

from bravado_core import schema
from bravado_core._compact import wraps
from bravado_core.exception import SwaggerMappingError
from bravado_core.model import MODEL_MARKER
from bravado_core.schema import collapsed_properties
from bravado_core.schema import get_type_from_schema
from bravado_core.schema import handle_null_value
from bravado_core.schema import is_dict_like
from bravado_core.schema import is_list_like
from bravado_core.schema import SWAGGER_PRIMITIVES
from bravado_core.util import memoize_by_id
from bravado_core.util import RecursiveCallException


_NOT_FOUND = object()


def unmarshal_schema_object(swagger_spec, schema_object_spec, value):
    """
    Unmarshal the value using the given schema object specification.

    Unmarshalling includes:
    - transform the value according to 'format' if available
    - return the value in a form suitable for use. e.g. conversion to a Model
      type.

    :type swagger_spec: :class:`bravado_core.spec.Spec`
    :type schema_object_spec: dict
    :type value: int, float, long, string, unicode, boolean, list, dict, etc

    :return: unmarshalled value
    :rtype: int, float, long, string, unicode, boolean, list, dict, object (in
        the case of a 'format' conversion', or Model type
    """
    unmarshaling_method = get_unmarshaling_method(swagger_spec, schema_object_spec)
    return unmarshaling_method(value)


class _handle_null_value_decorator(object):
    __slots__ = ('swagger_spec', 'object_schema', 'required')

    def __init__(self, swagger_spec, object_schema, required):
        self.swagger_spec = swagger_spec
        self.object_schema = object_schema
        self.required = required

    @staticmethod
    @memoize_by_id
    def decorator(swagger_spec, object_schema, required=True):
        return _handle_null_value_decorator(swagger_spec, object_schema, required)

    def __call__(self, func):
        @wraps(func)
        def wrapper(value, *args, **kwargs):
            if value is None:
                value = schema.get_default(self.swagger_spec, self.object_schema)
                if value is None:
                    return handle_null_value(self.swagger_spec, self.object_schema) if self.required else None
                else:
                    return value
            return func(value, *args, **kwargs)

        return wrapper


def _wrap_recursive_call_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RecursiveCallException:
            return lambda *new_args, **new_kawrgs: func(*args, **kwargs)(*new_args, **new_kawrgs)
    return wrapper


@_wrap_recursive_call_exception
@memoize_by_id
def get_unmarshaling_method(swagger_spec, object_schema, required=True):
    """
    Determine the method needed to unmarshal values of a defined object_schema
    The returned method will accept a single positional parameter that represent the value
    to be unmarshaled.

    :type swagger_spec: :class:`bravado_core.spec.Spec`
    :type object_schema: dict
    """
    object_schema = swagger_spec.deref(object_schema)
    null_decorator = _handle_null_value_decorator.decorator(swagger_spec, object_schema, required)
    object_type = get_type_from_schema(swagger_spec, object_schema)

    if object_type == 'array':
        return null_decorator(_unmarshaling_method_array(swagger_spec, object_schema))
    elif object_type == 'file':
        return null_decorator(_unmarshaling_method_file(swagger_spec, object_schema))
    elif object_type == 'object':
        return null_decorator(_unmarshaling_method_object(swagger_spec, object_schema))
    elif object_type in SWAGGER_PRIMITIVES:
        return null_decorator(_unmarshaling_method_primitive_type(swagger_spec, object_schema))
    elif object_type is None:
        return _no_op_unmarshaling
    else:
        return partial(_unknown_type_unmarhsaling, object_type)


def _no_op_unmarshaling(value):
    return value


def _unknown_type_unmarhsaling(object_type, value):
    raise SwaggerMappingError(
        "Don't know how to unmarshal value {0} with a type of {1}".format(
            value, object_type,
        ),
    )


def _raise_unknown_model(model_name, value):
    raise SwaggerMappingError('Unknown model {0} when trying to unmarshal {1}'.format(model_name, value))


def _unmarshal_array(unmarshal_array_item_function, value):
    """
    Unmarshal a jsonschema type of 'array' into a python list.

    :type unmarshal_array_item_function: callable
    :type value: list
    :rtype: list
    :raises: SwaggerMappingError
    """
    if not is_list_like(value):
        raise SwaggerMappingError('Expected list like type for {0}:{1}'.format(type(value), value))

    return [
        unmarshal_array_item_function(item)
        for item in value
    ]


def _unmarshaling_method_array(swagger_spec, object_schema):
    item_schema = swagger_spec.deref(swagger_spec.deref(object_schema).get('items', _NOT_FOUND))
    if item_schema is _NOT_FOUND:
        return _no_op_unmarshaling

    return partial(
        _unmarshal_array,
        get_unmarshaling_method(swagger_spec, item_schema),
    )


def _unmarshaling_method_file(swagger_spec, object_schema):
    return _no_op_unmarshaling


def _unmarshal_model(
    properties_to_unmarshaling_function,
    discriminator_property,
    model_to_unmarshaling_function_mapping,
    model_type,
    include_missing_properties,
    properties_to_default_value,
    required_properties,
    model_value,
):
    """
    Unmarshal a dict into a Model instance or a dictionary (according to the 'use_models' swagger_spec configuration).

    :type model_type: Model
    :type model_value: dict

    :rtype: Model instance
    :raises: SwaggerMappingError
    """
    if model_type is None:
        model_type = dict

    if not is_dict_like(model_value):
        raise SwaggerMappingError(
            "Expected type to be dict for value {0} to unmarshal to a {1}."
            "Was {2} instead."
            .format(model_value, model_type.__name__, type(model_value))
        )

    unamarshaled_value = model_type()

    if discriminator_property:
        discriminated_model_unsmarhaling_function = model_to_unmarshaling_function_mapping.get(
            model_value[discriminator_property]
        )
        if discriminated_model_unsmarhaling_function:
            return discriminated_model_unsmarhaling_function(model_value)

    for property_name, property_value in iteritems(model_value):
        # TODO: fix to handle additional properties schema
        unmarshaling_function = properties_to_unmarshaling_function.get(property_name, _no_op_unmarshaling)
        unamarshaled_value[property_name] = unmarshaling_function(property_value)

    if include_missing_properties:
        for property_name, unmarshaling_function in iteritems(properties_to_unmarshaling_function):
            if property_name not in unamarshaled_value:
                unamarshaled_value[property_name] = properties_to_default_value.get(property_name)

    return unamarshaled_value


def _unmarshaling_method_object(swagger_spec, object_schema):
    model_type = None
    object_schema = swagger_spec.deref(object_schema)
    if MODEL_MARKER in object_schema:
        model_name = object_schema[MODEL_MARKER]
        model_type = swagger_spec.definitions.get(model_name)

    if model_type is None:
        properties = collapsed_properties(object_schema, swagger_spec)
        required_properties = object_schema.get('required', [])
    else:
        properties = model_type._properties
        required_properties = model_type._required_properties

    properties_to_unmarshaling_function = {}
    for prop_name, prop_schema in iteritems(properties):
        properties_to_unmarshaling_function[prop_name] = get_unmarshaling_method(
            swagger_spec, prop_schema,
            required=prop_name in required_properties,
        )

    discriminator_property = object_schema.get('discriminator') if model_type is not None else None

    model_to_unmarshaling_function_mapping = None
    if discriminator_property is not None:
        model_to_unmarshaling_function_mapping = {
            k: get_unmarshaling_method(
                swagger_spec,
                v._model_spec,
            )
            for k, v in iteritems(swagger_spec.definitions)
            if model_type.__name__ in v._inherits_from
        }

    properties_to_default_value = {
        prop_name: schema.get_default(swagger_spec, prop_schema)
        for prop_name, prop_schema in iteritems(properties)
        if schema.has_default(swagger_spec, prop_schema)
    }

    return partial(
        _unmarshal_model,
        properties_to_unmarshaling_function,
        discriminator_property,
        model_to_unmarshaling_function_mapping,
        model_type if model_type and model_type._use_models else None,
        model_type._include_missing_properties if model_type else swagger_spec.config['include_missing_properties'],
        properties_to_default_value,
        required_properties,
    )


def _unmarshaling_method_primitive_type(swagger_spec, object_schema):
    try:
        swagger_format = schema.get_format(swagger_spec, object_schema)
        if swagger_format is not None:
            return swagger_spec.get_format(swagger_format).to_python
    except AttributeError:
        pass
    return _no_op_unmarshaling
