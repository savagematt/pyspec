from typing import Callable, Optional, Set, Iterable, Dict

import spec.impl.core as impl
from spec.impl.core import Spec, SpecResult, SimpleSpec, Explanation, path
from spec.impl.dicts import DictSpec
from spec.impl.iterables import CollOf
from spec.impl.specs import Any, EqualTo, IsInstance, Even, Odd, IsNone, Coerce, InRange, Gt, Lt, Gte, Lte, IsIn, Never, \
    OneOf, AllOf
from spec.impl.util.strings import a_or_an

Speccable = impl.Speccable

INVALID = impl.INVALID


# noinspection PyProtectedMember
def isvalid(x) -> bool:
    """
    Check where the result of spec.core.conform() to see whether the conform operation succeeded
    """
    return impl.isvalid(x)


# noinspection PyProtectedMember
def isinvalid(x) -> bool:
    """
    Check where the result of spec.core.conform() to see whether the conform operation failed
    """
    return impl.isinvalid(x)


def any_():
    """
    Spec that conforms any value to itself and never fails
    """
    return Any()


def never():
    """
    Spec that will fail to conform any value and always fails
    """
    return Never()


def equal_to(x: object) -> EqualTo:
    return EqualTo(x)


def is_instance(t: type) -> IsInstance:
    return IsInstance(t)


def even() -> Even:
    """
    An even number?
    """
    return Even()


def odd() -> Odd:
    """
    An odd number?
    """
    return Odd()


def is_none() -> IsNone:
    return IsNone()


def in_range(start, end_exclusive=None) -> InRange:
    return InRange(start, end_exclusive)


def gt(value) -> InRange:
    """
    Greater than
    """
    return Gt(value)


def lt(value) -> InRange:
    """
    Less than
    """
    return Lt(value)


def gte(value) -> InRange:
    """
    Greater than or equal to
    """
    return Gte(value)


def lte(value) -> InRange:
    """
    Less than or equal to
    """
    return Lte(value)


def is_in(coll: Iterable) -> IsIn:
    return IsIn(frozenset(coll))


def coerce(coercer: Callable[[object], object],
           s: Speccable,
           explain_coercion_failure: Callable[[object], str] = None) \
        -> Coerce:
    """
    Returns a spec that runs coercer over the value before passing it to spec for conformance and explanation

    If the coercion fails, you can override the default message by providing explain_coercion_failure
    """
    return Coerce(coercer, specize(s), explain_coercion_failure=explain_coercion_failure)


def decorated(x: Speccable, description: str = None):
    return impl.DecoratedSpec(specize(x), description=description)


def specize(x: Speccable) -> Spec:
    """
    Although this is public and in spec.core, you'll probably never need to use it
    """
    if isinstance(x, Spec):
        return x

    if isinstance(x, type):
        return is_instance(x)

    if isinstance(x, Set):
        return is_in(x)

    if callable(x):
        if hasattr(x, '__name__'):
            description = x.__name__
        elif hasattr(x, '__code__'):
            description = x.__code__.co_name
        else:
            description = a_or_an(type(x).__name__)

        return SimpleSpec(description, x)

    raise ValueError("I don't know how to turn a {} into a spec: {}".format(type(x), x))


# noinspection PyBroadException
def conform(s: Speccable, x: object) -> SpecResult:
    """
    Given a spec and a value, returns spec.core::INVALID if value does not match spec,
    else the (possibly destructured) value."
    """
    return specize(s).conform(x)


def explain_data(s: Speccable, x: object) -> Optional[Explanation]:
    """
    Given a spec and a value x which ought to conform, returns nil if x
    conforms, else an Explanation, which contains a collection of Problems
    """
    problems = specize(s).explain(path(), x)
    if problems is None or len(problems) == 0:
        return None
    return Explanation.with_problems(*problems)


def describe(s: Speccable) -> str:
    return specize(s).describe()


def isspec(x: object):
    return isinstance(x, Spec)


def assert_spec(s: Speccable, x: object) -> object:
    return impl.assert_spec(specize(s),x)


def coll_of(s: Speccable):
    return CollOf(specize(s))


def one_of(*ss: Speccable):
    return OneOf([specize(s) for s in ss])


def all_of(*ss: Speccable):
    return AllOf([specize(s) for s in ss])


def dict_spec(d: Dict[object, Speccable]):
    def f(x):
        if isinstance(x, dict):
            return dict_spec(x)
        else:
            return specize(x)

    return DictSpec({k: f(v) for k, v in d.items()})


def dict_example(d: Dict[object, Speccable]):
    def f(x):
        try:
            x = specize(x)
        except:
            pass

        if isspec(x):
            return x
        elif isinstance(x, dict):
            return dict_example(x)
        else:
            return equal_to(x)

    return dict_spec(({k: f(v) for k, v in d.items()}))
