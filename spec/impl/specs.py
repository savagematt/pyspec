from typing import Callable, List, Iterable

from spec.impl.core import Spec, SpecResult, SimpleSpec, DelegatingSpec, Problem, Path, INVALID, isvalid, \
    isinvalid
from spec.impl.util.strings import a_or_an


class Any(Spec):
    def conform(self, x) -> SpecResult:
        return x

    def explain(self, p: Path, x: object) -> List[Problem]:
        return []

    def describe(self) -> str:
        return "anything"


class Never(Spec):
    def conform(self, x) -> SpecResult:
        return INVALID

    def explain(self, p: Path, x: object) -> List[Problem]:
        return [Problem(p, x, self, "this spec will always fail")]

    def describe(self) -> str:
        return "this spec will always fail"


class EqualTo(SimpleSpec):
    def __init__(self, value):
        super().__init__(str(value),
                         lambda x: x == value,
                         lambda x: "expected {} ({}) but got {} ({})".format(value, type(value).__name__, x,
                                                                             type(x).__name__))
        self._value = value

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._value == other._value
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __hash__(self):
        return hash(self._value)


class IsInstance(SimpleSpec):
    def __init__(self, cls):
        description = a_or_an(cls.__name__)
        super().__init__(description,
                         lambda x: isinstance(x, cls),
                         lambda x: "expected {} but got {}".format(description, a_or_an(type(x).__name__)))
        self._cls = cls

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._cls == other._cls
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __hash__(self):
        return hash(self._cls)


def Even() -> Spec:
    return SimpleSpec("an even number",
                      lambda x: isinstance(x, int) and not bool(x & 1))


def Odd() -> Spec:
    return SimpleSpec("an odd number",
                      lambda x: isinstance(x, int) and bool(x & 1))


def IsNone() -> Spec:
    return SimpleSpec("None",
                      lambda x: x is None)


def InRange(start, end_exclusive=None) -> Spec:
    return SimpleSpec("between {} {}".format(start, "and {}".format(end_exclusive) if end_exclusive else None),
                      lambda x: x >= start and (end_exclusive is None or x < end_exclusive))


def Gt(value) -> Spec:
    return SimpleSpec("greater than {}".format(value),
                      lambda x: x > value)


def Lt(value) -> Spec:
    return SimpleSpec("less than {}".format(value),
                      lambda x: x < value)


def Gte(value) -> Spec:
    return SimpleSpec("greater than or equal to {}".format(value),
                      lambda x: x >= value)


def Lte(value) -> Spec:
    return SimpleSpec("less than or equal to {}".format(value),
                      lambda x: x <= value)


class IsIn(Spec):
    def __init__(self, coll: Iterable):
        coll = frozenset(coll)

        self._coll = coll
        self._coll_for_explain = list(sorted(coll))

    def describe(self) -> str:
        return "in {}".format(self._coll_for_explain)

    def explain(self, p: Path, x: object) -> List[Problem]:
        if x in self._coll:
            return []
        else:
            return [Problem(p, x, self, "not {}".format(self.describe()))]

    def conform(self, x: object) -> SpecResult:
        return x if x in self._coll else INVALID

    def __eq__(self, other):
        """Override the default Equals behavior"""
        if isinstance(other, self.__class__):
            return self._coll == other._coll
        return NotImplemented

    def __ne__(self, other):
        """Define a non-equality test"""
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __hash__(self):
        """Override the default hash behavior (that returns the id or the object)"""
        return hash(self._coll)


Coercer = Callable[[object], object]


def name_of(x):
    if hasattr(x, '__code__'):
        return x.__code__.co_name
    elif hasattr(x, '__name__'):
        return x.__name__
    else:
        return type(x).__name__


def _default_coercion_explainer(coercer: Coercer):
    return lambda x, e: "could not coerce '{}' ({}) using coercer: {} because:\n{}" \
        .format(x, type(x).__name__, name_of(coercer), e)


class Coerce(DelegatingSpec):
    def __init__(self,
                 coercer: Coercer,
                 spec: Spec,
                 explain_coercion_failure: Callable[[object], str] = None):
        super().__init__(spec)
        self._coercer = coercer
        self._explain_coercion_failure = explain_coercion_failure or _default_coercion_explainer(coercer)

    def conform(self, x) -> SpecResult:
        # noinspection PyBroadException
        try:
            c = self._coercer(x)
        except:
            return INVALID
        else:
            return super().conform(c)

    def explain(self, p: Path, x: object) -> List[Problem]:
        # noinspection PyBroadException
        try:
            c = self._coercer(x)
        except Exception as e:
            return [Problem(p, x, self, self._explain_coercion_failure(x, e))]
        else:
            return super().explain(p, c)


class OneOf(Spec):
    def __init__(self, specs: Iterable[Spec]):
        self._specs = specs

    def conform(self, x) -> SpecResult:
        for s in self._specs:
            r = s.conform(x)
            if isvalid(r):
                return r
        return INVALID

    def describe(self) -> str:
        return "one of {}".format([s.describe() for s in self._specs])

    def explain(self, p: Path, x: object) -> List[Problem]:
        problems = []
        for s in self._specs:
            ps = s.explain(p, x)
            problems.extend(ps)
        return problems


class AllOf(Spec):
    def __init__(self, specs: Iterable[Spec]):
        self._specs = specs

    def conform(self, x) -> SpecResult:
        for s in self._specs:
            x = s.conform(x)
            if isinvalid(x):
                return x
        return x

    def describe(self) -> str:
        return "all of {}".format([s.describe() for s in self._specs])

    def explain(self, p: Path, x: object) -> List[Problem]:
        for s in self._specs:
            x = s.conform(x)
            if isinvalid(x):
                return s.explain(p, x)
        return []
