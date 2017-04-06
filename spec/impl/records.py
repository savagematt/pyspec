from pprint import pformat
from typing import TypeVar, Union, Callable, List, Mapping

from spec.core import is_instance, all_of, one_of, coll_of
from spec.impl import specs as sis
from spec.impl.core import Spec, Path, Problem, SpecResult, INVALID, isinvalid
from spec.impl.dicts import DictSpec
from spec.impl.util.forwardref import is_forward_ref, resolve_forward_ref
from spec.impl.util.typevars import extract_typevars
from spec.impl.util.annotations import AnnotationContext, extract_annotations


class UnboundTypeVar:
    def __init__(self, t: TypeVar):
        super().__init__()
        self.typevar = t


def resolve_typevar(a: AnnotationContext) -> Union[AnnotationContext, UnboundTypeVar]:
    n = a.annotation.__name__
    if n in a.typevars_from_class:
        t = a.typevars_from_class[n]
    else:
        t = TypeVar(n)
    if isinstance(t, TypeVar):
        return UnboundTypeVar(t)
    else:
        return AnnotationContext(t, a.class_annotation_was_on, a.typevars_from_class)


class DeferredSpec(Spec):
    def __init__(self, factory: Callable, hint_resolver: Callable[[], type]):
        super().__init__()
        self._factory = factory
        self._hint_resolver = hint_resolver
        self._resolved_spec = None

    def _resolve_spec(self) -> Spec:
        if not self._resolved_spec:
            resolved_hint = self._hint_resolver()
            self._resolved_spec = self._factory(resolved_hint)
        return self._resolved_spec

    def describe(self) -> str:
        return self._resolve_spec().describe()

    def explain(self, p: Path, x: object) -> List[Problem]:
        return self._resolve_spec().explain(p, x)

    def conform(self, x: object) -> SpecResult:
        return self._resolve_spec().conform(x)


class UnboundTypeVarSpec(sis.Any):
    def __init__(self, typevar: TypeVar):
        super().__init__()
        self.typevar = typevar


class UnboundTypeVarDictSpec(Spec):
    _NOT_FOUND = object()

    def __init__(self, unbound_typevar_keys, spec_generator):
        super().__init__()
        typevar_to_attr_names = {}
        for attr_name, typevar in unbound_typevar_keys.items():
            if not typevar in typevar_to_attr_names:
                typevar_to_attr_names[typevar] = []
            typevar_to_attr_names[typevar].append(attr_name)
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


def spec_from(x: Union[AnnotationContext, type]):
    if x is None:
        return is_instance(type(None))

    if isinstance(x, type):
        if issubclass(x, Record):
            annotations = extract_annotations(x)
            specs = {}
            for attr, annotation in annotations.items():
                specs[attr] = spec_from(annotation)

            typevars = extract_typevars(x)
            unbound_typevars = {k: v for k, v in typevars.items() if isinstance(v, TypeVar)}
            if not unbound_typevars:
                return DictSpec(specs)
            else:
                unbound_type_var_keys = {k: v.typevar for k, v in specs.items() if isinstance(v, UnboundTypeVarSpec)}
                return all_of(DictSpec(specs), UnboundTypeVarDictSpec(unbound_type_var_keys, spec_from))
        else:
            return is_instance(x)

    if isinstance(x, UnboundTypeVar):
        return UnboundTypeVarSpec(x.typevar)

    if isinstance(x, AnnotationContext):
        if type(x.annotation) == type(Union):
            return one_of(*[spec_from(AnnotationContext(a, x.class_annotation_was_on, x.typevars_from_class)) for a in x.annotation.__args__])

        elif is_forward_ref(x):
            return DeferredSpec(spec_from, lambda: resolve_forward_ref(x))

        elif isinstance(x.annotation, TypeVar):
            return spec_from(resolve_typevar(x))

        elif issubclass(x.annotation, List):
            return coll_of(spec_from(AnnotationContext(x.annotation.__args__[0], x.class_annotation_was_on, x.typevars_from_class)))

        else:
            return is_instance(x.annotation)

    raise NotImplementedError("Can't produce a spec from {}".format(x))


class Record:
    pass