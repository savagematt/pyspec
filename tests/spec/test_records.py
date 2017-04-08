from typing import List, Optional, TypeVar, Generic

from spec.core import assert_spec
from spec.impl.core import SpecError
from spec.impl.records.core import spec_from, Record


def check_spec_error(s, value, expected_error_text):
    try:
        assert_spec(s, value)
        assert False, "Expected exception"
    except SpecError as e:
        assert expected_error_text in str(e)


class JustPrimitive(Record):
    k: int


def test_primitives():
    s = spec_from(JustPrimitive)

    d = assert_spec(s, {'k': 123})

    assert d == {'k': 123}

    check_spec_error(s, {'k': "not an int"}, "not an int")


class SingleGenericField(Record):
    k: List[int]


def test_generics():
    s = spec_from(SingleGenericField)

    d = assert_spec(s, {'k': [123, 456]})

    assert d == {'k': [123, 456]}

    check_spec_error(s, {'k': ["not an int"]}, "not an int")


class WithOptional(Record):
    k: Optional[int]


def test_optional():
    s = spec_from(WithOptional)

    assert assert_spec(s, {'k': 123}) == {'k': 123}
    assert assert_spec(s, {'k': None}) == {'k': None}

    check_spec_error(s, {'k': "not an int"}, "not an int")


class NeedsForwardReference(Record):
    k: Optional['NeedsForwardReference']


def test_forward_references():
    s = spec_from(NeedsForwardReference)

    d = assert_spec(s, {'k': {'k': None}})

    assert d == {'k': {'k': None}}

    check_spec_error(s, {'k': "not a NeedsForwardReference"}, "not a NeedsForwardReference")


class ListsOfForwardReference(Record):
    k: List['ListsOfForwardReference']


def test_lists_of_forward_references():
    s = spec_from(ListsOfForwardReference)

    d = assert_spec(s, {'k': [{'k': []}]})

    assert d == {'k': [{'k': []}]}

    check_spec_error(s, {'k': ["not a NeedsForwardReference"]}, "not a NeedsForwardReference")


T = TypeVar('T')
V = TypeVar('V')


class GenericClass(Generic[T, V], Record):
    t: T
    v: V


class BoundGenericClass(GenericClass[int, str]):
    pass


def test_generic_typevars_unconstrained_bound():
    s = spec_from(BoundGenericClass)

    d = assert_spec(s, {'t': 123, 'v': 'string'})

    assert d == {'t': 123, 'v': 'string'}

    check_spec_error(s, {'t': "not an int", 'v': 'string'}, "not an int")


class UnboundGenericClass(GenericClass[int, V]):
    another_v: V


def test_generic_typevars_unconstrained_unbound():
    s = spec_from(UnboundGenericClass)

    d = assert_spec(s, {'t': 123, 'v': "V type", 'another_v': "V type"})

    assert d == {'t': 123, 'v': "V type", 'another_v': "V type"}

    # Should not conform if all annotations marked with unbound generic V
    # are not of the same type
    int_V = 123
    str_V = "mooooo"
    check_spec_error(s, {'t': 123, 'v': int_V, 'another_v': str_V}, str_V)


class NonGenericClassWithTypevars(Record):
    a: T
    b: T


def test_non_generic_class_with_typevar_annotations():
    s = spec_from(NonGenericClassWithTypevars)

    d = assert_spec(s, {'a': 123, 'b': 456})

    assert d == {'a': 123, 'b': 456}

    # Need to ensure all annotations marked with unbound generic V
    # are of the same type
    int_T = 123
    str_T = "mooooo"
    check_spec_error(s, {'a': int_T, 'b': str_T}, str_T)