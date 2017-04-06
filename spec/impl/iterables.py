from typing import Iterable, List

from spec.impl.core import Spec, SpecResult, Problem, Path, isinvalid, INVALID


class CollOf(Spec):
    def __init__(self, itemspec: Spec):
        super().__init__()
        self._itemspec = itemspec

    def conform(self, xs: Iterable) -> SpecResult:
        if not hasattr(xs, '__iter__'):
            return INVALID

        result = []
        for x in xs:
            v = self._itemspec.conform(x)
            if isinvalid(v):
                return INVALID
            result.append(v)

        if isinstance(xs, tuple):
            return tuple(result)
        else:
            return result

    def describe(self) -> str:
        return "a collection where items are {}".format(self._itemspec.describe())

    def explain(self, p: Path, xs: Iterable) -> List[Problem]:
        if not hasattr(xs, '__iter__'):
            return [Problem(p, xs, self, "not iterable")]
        result = []
        for i, x in enumerate(xs):
            problems = self._itemspec.explain(p + (i,), x)
            if problems:
                result.extend(problems)
        return result
