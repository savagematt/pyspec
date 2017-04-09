from typing import TypeVar, Union, List, _ForwardRef

from spec.core import is_instance, all_of, one_of, coll_of
from spec.impl.dicts import DictSpec
from spec.impl.records.annotations import AnnotationContext, extract_annotations
from spec.impl.records.forwardrefs import resolve_forward_ref, DeferredSpecFromForwardReference
from spec.impl.records.typevars import UnboundTypeVar, UnboundTypeVarSpec, UnboundTypeVarDictSpec, _typevar_key


def resolve_typevar(a: AnnotationContext) -> Union[AnnotationContext, UnboundTypeVar]:
    n = a.annotation.__name__

    if n not in a.typevars_from_class:
        return UnboundTypeVar(a.annotation)

    bound_to = a.typevars_from_class[n]
    if isinstance(bound_to, TypeVar) and _typevar_key(bound_to) == _typevar_key(a.annotation):
        return UnboundTypeVar(bound_to)
    else:
        return AnnotationContext(bound_to, a.class_annotation_was_on, a.typevars_from_class)


def spec_from(x: Union[AnnotationContext, type]):
    if x is None:
        return is_instance(type(None))

    if isinstance(x, type):
        if issubclass(x, Record):
            annotations = extract_annotations(x)
            specs = {}
            for attr, annotation in annotations.items():
                specs[attr] = spec_from(annotation)

            unbound_typevars = {k: v.typevar for k, v in specs.items() if isinstance(v, UnboundTypeVarSpec)}

            if unbound_typevars:
                return all_of(DictSpec(specs), UnboundTypeVarDictSpec(unbound_typevars, spec_from))
            else:
                return DictSpec(specs)
        else:
            return is_instance(x)

    if isinstance(x, UnboundTypeVar):
        return UnboundTypeVarSpec(x.typevar)

    if isinstance(x, AnnotationContext):
        if type(x.annotation) == type(Union):
            return one_of(*[spec_from(x.for_hint(a))
                            for a in x.annotation.__args__])

        elif isinstance(x.annotation, _ForwardRef) or isinstance(x.annotation, str):
            return DeferredSpecFromForwardReference(spec_from, lambda: resolve_forward_ref(x))

        elif isinstance(x.annotation, TypeVar):
            return spec_from(resolve_typevar(x))

        elif issubclass(x.annotation, List):
            return coll_of(spec_from(x.for_hint(x.annotation.__args__[0])))

        else:
            return spec_from(x.annotation)

    raise NotImplementedError("Can't produce a spec from {}".format(x))


class Record:
    pass
