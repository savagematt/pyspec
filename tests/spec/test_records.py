from typing import List, Optional, TypeVar, Generic

import pytest

from spec.core import assert_spec
from spec.impl.core import SpecError
from spec.impl.records import spec_from, Record


class JustPrimitive(Record):
    k: int


def check_spec_error(s, value, expected_error_text):
    try:
        assert_spec(s, value)
        assert False, "Expected exception"
    except SpecError as e:
        assert expected_error_text in str(e)


def test_primitives():
    s = spec_from(JustPrimitive)

    d = assert_spec(s, {'k': 123})

    assert d == {'k': 123}

    check_spec_error(s, {'k': "not an int"}, "not an int")


class HasGenericField(Record):
    k: List[int]


def test_generics():
    s = spec_from(HasGenericField)

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

    d = assert_spec(s, {'k': [{'k': [{'k': []}, {'k': []}]}]})

    assert d == {'k': [{'k': [{'k': []}, {'k': []}]}]}

    check_spec_error(s, {'k': ["not a NeedsForwardReference"]}, "not a NeedsForwardReference")


A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
D = TypeVar('D')
E = TypeVar('E')

T = TypeVar('T')
V = TypeVar('V')


class GenericClass(Generic[T, V], Record):
    t: T
    v: V


class GenericClassImpl(GenericClass[int, str]):
    pass


def test_simpleish_generic_classes():
    s = spec_from(GenericClassImpl)

    d = assert_spec(s, {'t': 123, 'v': 'string'})

    assert d == {'t': 123, 'v': 'string'}

    check_spec_error(s, {'t': "not an int", 'v': 'string'}, "not an int")


class MultipleGeneric(Generic[T, V], Record):
    a: T
    b: V


class MultiImplA(MultipleGeneric[int, V]):
    c: V


def test_generic_classes_with_unbound_typevars():
    s = spec_from(MultiImplA)

    d = assert_spec(s, {'a': 123, 'b': "V type", 'c': "V type"})

    assert d == {'a': 123, 'b': "V type", 'c': "V type"}

    # Need to ensure all annotations marked with unbound generic V
    # are of the same type
    int_V = 123
    str_V = "mooooo"
    check_spec_error(s, {'a': 123, 'b': int_V, 'c': str_V}, str_V)


def test_generic_classes_with_just_in_time_bound_typevars():
    s = spec_from(MultiImplA[int])

    d = assert_spec(s, {'a': 123, 'b': 456, 'c': 789})

    assert d == {'a': 123, 'b': 456, 'c': 789}

    check_spec_error(s, {'a': 123, 'b': 456, 'c': "wrong type"}, "wrong type")


class SomeOtherGeneric(Record):
    a: T
    b: T


@pytest.mark.skip(reason="WIP")
def test_unbound_typevars():
    s = spec_from(SomeOtherGeneric)

    d = assert_spec(s, {'a': 123, 'b': 456})

    assert d == {'a': 123, 'b': 456}

    # Need to ensure all annotations marked with unbound generic V
    # are of the same type
    int_T = 123
    str_T = "mooooo"
    check_spec_error(s, {'a': int_T, 'b': str_T}, str_T)
