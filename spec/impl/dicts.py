import pprint
from typing import Dict, List

from spec.impl.core import Spec, SpecResult, Path, Problem, path, INVALID, isinvalid
from spec.impl.specs import EqualTo


def isspec(x: object):
    return isinstance(x, Spec)


def _value_spec(possibly_a_spec):
    if isspec(possibly_a_spec):
        return possibly_a_spec
    elif isinstance(possibly_a_spec, dict):
        return DictSpec(possibly_a_spec)
    else:
        return EqualTo(possibly_a_spec)


def _acceptably_dict_like(x):
    return isinstance(x, dict) or not [a for a in {'__getitem__', '__iter__', '__contains__'} if not hasattr(x, a)]


class DictSpec(Spec):
    def __init__(self, key_to_spec: Dict[object, Spec]):
        self._key_to_spec = key_to_spec

    def describe(self) -> str:
        return "Dict:\n{}".format(pprint.pformat(self._key_to_spec))

    def conform(self, x: Dict) -> SpecResult:
        if not _acceptably_dict_like(x):
            return INVALID

        result = {}
        for k, s in self._key_to_spec.items():
            if not k in x:
                return INVALID

            value = x[k]

            conformed = s.conform(value)
            if isinvalid(conformed):
                return INVALID
            result[k] = conformed

        return result

    def explain(self, p: Path, x: object) -> List[Problem]:
        if not _acceptably_dict_like(x):
            return [Problem(p, x, self, "not a dictionary {}".format(type(x)))]

        problems = []
        for k, s in self._key_to_spec.items():
            if k not in x:
                problems.append("Missing {}".format(k))
                continue

            value = x[k]
            explanation_path = p + path(k)

            subspec_problems = s.explain(explanation_path, value)
            if subspec_problems:
                problems.extend(subspec_problems)

        return problems
