from pprint import pformat

from typing import TypeVar, List, Mapping

from spec.impl import specs as sis
from spec.impl.core import Spec, Path, Problem, SpecResult, INVALID, isinvalid


def generic_class_typevars(cls: type):
    typevars = {}
    for klass in cls.mro():
        for orig_base in getattr(klass, '__orig_bases__', []):
            for parameter, arg in extract_generic_parameters(orig_base):
                typevars[parameter.__name__] = arg
    return typevars


def extract_generic_parameters(cls: type):
    return map(lambda p, a: (p, a),
               getattr(getattr(cls, '__origin__', None), '__parameters__', []),
               getattr(cls, '__args__', []))


class UnboundTypeVar:
    def __init__(self, t: TypeVar):
        super().__init__()
        self.typevar = t


class UnboundTypeVarSpec(sis.Any):
    def __init__(self, typevar: TypeVar):
        super().__init__()
        self.typevar = typevar


def _typevar_key(t: TypeVar):
    """
    If I define a class like this:

    T=TypeVar('T')
    class Foo:
        a: T
        b: T

    ...then the two annotations on a and b are two different instances of TypeVar

    TypeVars are not hashable and don't implement __eq__, so it's not possible to use this mechanism to detect that
    the two annotations are the same, so we need to create a key from each TypeVar.
    """
    return tuple(getattr(t, s) for s in t.__slots__)


class UnboundTypeVarDictSpec(Spec):
    _NOT_FOUND = object()

    def __init__(self, unbound_typevar_keys, spec_generator):
        super().__init__()

        typevar_to_attr_names = {}
        for attr_name, typevar in unbound_typevar_keys.items():
            tvk = _typevar_key(typevar)
            if not tvk in typevar_to_attr_names:
                typevar_to_attr_names[tvk] = []
            typevar_to_attr_names[tvk].append(attr_name)

        self._typevar_to_attr_names = typevar_to_attr_names
        self._spec_generator = spec_generator

    def describe(self) -> str:
        return "all typevars should be the same: {}".format(pformat(self._typevar_to_attr_names))

    def explain(self, p: Path, x: object) -> List[Problem]:
        if not isinstance(x, Mapping):
            return [Problem(p, x, self, "not a Mapping")]

        problems = []
        for typevar, names in self._typevar_to_attr_names.items():
            first_name_found = next((name for name in names if name in x), None)
            implied_type = type(x[first_name_found]) if first_name_found else None
            s = self._spec_generator(implied_type)
            for name in names:
                value = x[name]
                ps = s.explain(p, value)
                problems.extend(ps)
        return problems

    def conform(self, x: object) -> SpecResult:
        if not isinstance(x, Mapping):
            return INVALID

        result = dict(x)
        for typevar, names in self._typevar_to_attr_names.items():
            first_name_found = next((name for name in names if name in x), None)
            implied_type = type(x[first_name_found]) if first_name_found else None
            s = self._spec_generator(implied_type)
            for name in names:
                value = s.conform(x[name])
                if isinvalid(value):
                    return INVALID
                result[name] = value
        return result