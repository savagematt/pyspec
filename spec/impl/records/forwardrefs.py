import sys
from typing import _ForwardRef, Callable, List, Union

from spec.impl.core import Spec, Path, Problem, SpecResult
from spec.impl.records.annotations import AnnotationContext


def resolve_forward_ref(ac: AnnotationContext):
    typeref = ac.annotation
    if isinstance(typeref, _ForwardRef):
        typeref = ac.annotation.__forward_arg__

    module = sys.modules[ac.class_annotation_was_on.__module__]

    if isinstance(typeref, str):
        # noinspection PyUnresolvedReferences
        if hasattr(module, typeref):
            return getattr(module, typeref)
        elif typeref in __builtins__:
            # noinspection PyUnresolvedReferences
            return __builtins__[typeref]
        else:
            raise NameError("name '{}' is not defined in '{}'".format(
                typeref, module.__name__
            ))
    else:
        return typeref


class DeferredSpecFromForwardReference(Spec):
    def __init__(self, spec_factory: Callable[[type], Spec], forward_reference_resolver: Callable[[], type]):
        super().__init__()
        self._spec_factory = spec_factory
        self._forward_reference_resolver = forward_reference_resolver
        self._resolved_spec = None

    def _resolve_spec(self) -> Spec:
        if not self._resolved_spec:
            resolved_hint = self._forward_reference_resolver()
            self._resolved_spec = self._spec_factory(resolved_hint)
        return self._resolved_spec

    def describe(self) -> str:
        return self._resolve_spec().describe()

    def explain(self, p: Path, x: object) -> List[Problem]:
        return self._resolve_spec().explain(p, x)

    def conform(self, x: object) -> SpecResult:
        return self._resolve_spec().conform(x)
