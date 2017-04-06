from abc import ABCMeta, abstractmethod
from pprint import pformat
from typing import Callable, Union, List, Iterable, Set, NamedTuple, Dict
from typing import Tuple

from spec.impl.util.callables import can_be_called_with_one_argument


class Invalid:
    def __str__(self, *args, **kwargs):
        return repr(self)

    def __repr__(self):
        return "<INVALID>"

    def __hash__(self):
        return 42

    def __eq__(self, other):
        return isinstance(other, Invalid)

    def __ne__(self, other):
        return not self.__eq__(other)


INVALID = Invalid()


def isvalid(x) -> bool:
    return INVALID != x


def isinvalid(x) -> bool:
    return not isvalid(x)


SpecResult = Union[Invalid, object]
PathElement = Union[str, int, object]
Path = Tuple[PathElement, ...]


def path(*elements: Iterable[PathElement]) -> Path:
    return tuple(elements)


class Problem(NamedTuple):
    path: Path
    value: object
    spec: 'Spec'
    reason: str


class Explanation:
    @classmethod
    def with_problems(cls, *problems: Iterable[Problem]) -> 'Explanation':
        return Explanation(problems)

    def __init__(self, problems: Iterable[Problem]):
        self._problems = tuple(problems)

    @property
    def problems(self) -> Tuple[Problem, ...]:
        return self._problems

    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented

        return self.problems == other.problems

    def __ne__(self, other):
        return not self == other

    def __hash__(self, *args, **kwargs):
        return hash(self.problems)

    def __str__(self, *args, **kwargs):
        return pformat(self._problems)


class SpecError(RuntimeError):
    def __init__(self, value: object, explanation: Explanation):
        RuntimeError.__init__(self, "\nValue:\n{}\n\nProblems:\n{}".format(value, explanation))
        self._value = value
        self._explanation = explanation

    @property
    def explanation(self) -> Explanation:
        return self._explanation

    @property
    def value(self) -> object:
        return self._value


class Spec(metaclass=ABCMeta):
    @abstractmethod
    def conform(self, x: object) -> SpecResult:
        raise NotImplementedError()

    @abstractmethod
    def explain(self, p: Path, x: object) -> List[Problem]:
        raise NotImplementedError()

    @abstractmethod
    def describe(self) -> str:
        raise NotImplementedError()

    def __str__(self, *args, **kwargs):
        return self.describe()


class DelegatingSpec(Spec):
    def __init__(self, delegate: Spec):
        self._delegate = delegate

    def conform(self, x) -> SpecResult:
        return self._delegate.conform(x)

    def explain(self, p: Path, x: object) -> List[Problem]:
        return self._delegate.explain(p, x)

    def describe(self) -> str:
        return self._delegate.describe()


class DecoratedSpec(DelegatingSpec):
    def __init__(self, delegate: Spec, description: str = None):
        super().__init__(delegate)
        self._description = description

    def describe(self) -> str:
        return self._description or super().describe()


class SimpleSpec(Spec):
    """
    Static description

    Unless overridden, explain returns a single problem with reason "not {description}" if check fails

    Wraps a simple (object) -> bool predicate
    """

    def __init__(self,
                 description: str,
                 check: Callable[[object], bool],
                 explain: Callable[[object], str] = None):
        super().__init__()
        explain = explain or (lambda x: "not {}".format(description))
        # noinspection PyTypeChecker
        if not can_be_called_with_one_argument(check):
            raise TypeError("Expected arity 1 callable as check but got {}".format(check))

        # noinspection PyTypeChecker
        if not can_be_called_with_one_argument(explain):
            raise TypeError("Expected arity 1 callable as explain but got {}".format(explain))

        self._description = description  # type:str
        self._explain = explain
        self._check = check  # type:Callable[[object], bool]

    def conform(self, x) -> SpecResult:
        if self._check(x):
            return x
        return INVALID

    def explain(self, p: Path, x: object) -> List[Problem]:
        if self._check(x):
            return []
        return [Problem(p, x, self, self._explain(x))]

    def describe(self) -> str:
        return self._description


PredFn = Callable[[object], bool]
Speccable = Union[Spec, PredFn, Set, Dict]


def assert_spec(s: Spec, x: object):
    conformed = s.conform(x)
    if isvalid(conformed):
        return conformed
    raise SpecError(x, Explanation.with_problems(*s.explain(path(), x)))
