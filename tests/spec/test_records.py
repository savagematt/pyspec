import pytest
from typing import List, Optional, TypeVar, Generic, Any, ClassVar

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


class HasList(Record):
    k: List[int]


def test_list():
    s = spec_from(HasList)

    d = assert_spec(s, {'k': [123, 456]})

    assert d == {'k': [123, 456]}

    check_spec_error(s, {'k': ["not an int"]}, "not an int")


class HasOptional(Record):
    k: Optional[int]


def test_optional():
    s = spec_from(HasOptional)

    assert assert_spec(s, {'k': 123}) == {'k': 123}
    assert assert_spec(s, {'k': None}) == {'k': None}

    check_spec_error(s, {'k': "not an int"}, "not an int")


class HasForwardReference(Record):
    k: Optional['HasForwardReference']


def test_forward_references():
    s = spec_from(HasForwardReference)

    d = assert_spec(s, {'k': {'k': None}})

    assert d == {'k': {'k': None}}

    check_spec_error(s, {'k': "not a NeedsForwardReference"}, "not a NeedsForwardReference")


class HasListsOfForwardReference(Record):
    k: List['HasListsOfForwardReference']


def test_lists_of_forward_references():
    s = spec_from(HasListsOfForwardReference)

    d = assert_spec(s, {'k': [{'k': []}]})

    assert d == {'k': [{'k': []}]}

    check_spec_error(s, {'k': ["not a NeedsForwardReference"]}, "not a NeedsForwardReference")


T = TypeVar('T')
V = TypeVar('V')


class IsGenericSuperclass(Generic[T, V], Record):
    t: T
    v: V


class BoundGeneric(IsGenericSuperclass[int, str]):
    pass


def test_generic_typevars_unconstrained_bound():
    s = spec_from(BoundGeneric)

    d = assert_spec(s, {'t': 123, 'v': 'string'})

    assert d == {'t': 123, 'v': 'string'}

    check_spec_error(s, {'t': "not an int", 'v': 'string'}, "not an int")


class UnboundGeneric(IsGenericSuperclass[int, V]):
    another_v: V


def test_generic_typevars_unconstrained_unbound():
    s = spec_from(UnboundGeneric)

    d = assert_spec(s, {'t': 123, 'v': "V type", 'another_v': "V type"})

    assert d == {'t': 123, 'v': "V type", 'another_v': "V type"}

    # Should not conform if all annotations marked with unbound generic V
    # are not of the same type
    int_V = 123
    str_V = "mooooo"
    check_spec_error(s, {'t': 123, 'v': int_V, 'another_v': str_V}, str_V)


class NonGenericWithTypevars(Record):
    a: T
    b: T


def test_non_generic_class_with_typevar_annotations():
    s = spec_from(NonGenericWithTypevars)

    d = assert_spec(s, {'a': 123, 'b': 456})

    assert d == {'a': 123, 'b': 456}

    # Need to ensure all annotations marked with unbound generic V
    # are of the same type
    int_T = 123
    str_T = "mooooo"
    check_spec_error(s, {'a': int_T, 'b': str_T}, str_T)


class HasAny(Record):
    a: Any


def test_any():
    s = spec_from(HasAny)

    d = assert_spec(s, {'a': "Whatever"})

    assert d == {'a': "Whatever"}


class HasClassVar(Record):
    a: ClassVar[int]


@pytest.mark.skip(reason="wip")
def test_classvar_should_never_appear():
    s = spec_from(HasClassVar)

    d = assert_spec(s, {})

    assert d == {}

    check_spec_error(s, {'a': 123}, "ClassVar")
    check_spec_error(s, {'a': "wrong type doesn't matter"}, "ClassVar")

    # # Super-special typing primitives.
    #     'Callable',
    #     'ClassVar',
    #     'Generic',
    #     'Optional',
    #     'Tuple',
    #     'Type',
    #     'TypeVar',
    #     'Union',
    #
    #     # ABCs (from collections.abc).
    #     'AbstractSet',  # collections.abc.Set.
    #     'ByteString',
    #     'Container',
    #     'Hashable',
    #     'ItemsView',
    #     'Iterable',
    #     'Iterator',
    #     'KeysView',
    #     'Mapping',
    #     'MappingView',
    #     'MutableMapping',
    #     'MutableSequence',
    #     'MutableSet',
    #     'Sequence',
    #     'Sized',
    #     'ValuesView',
    #     # The following are added depending on presence
    #     # of their non-generic counterparts in stdlib:
    #     # Awaitable,
    #     # AsyncIterator,
    #     # AsyncIterable,
    #     # Coroutine,
    #     # Collection,
    #     # ContextManager
    #
    #     # Structural checks, a.k.a. protocols.
    #     'Reversible',
    #     'SupportsAbs',
    #     'SupportsFloat',
    #     'SupportsInt',
    #     'SupportsRound',
    #
    #     # Concrete collection types.
    #     'Dict',
    #     'DefaultDict',
    #     'List',
    #     'Set',
    #     'FrozenSet',
    #     'NamedTuple',  # Not really a type.
    #     'Generator',
    #
    #     # One-off things.
    #     'AnyStr',
    #     'cast',
    #     'get_type_hints',
    #     'NewType',
    #     'no_type_check',
    #     'no_type_check_decorator',
    #     'overload',
    #     'Text',
    #     'TYPE_CHECKING',
