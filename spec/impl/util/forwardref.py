import sys
from typing import _ForwardRef

from spec.impl.util.annotations import AnnotationContext


def is_forward_ref(ac: AnnotationContext):
    return isinstance(ac.annotation, _ForwardRef) or isinstance(ac.annotation, str)


def resolve_forward_ref(ac: AnnotationContext):
    typeref = ac.annotation
    if isinstance(typeref, _ForwardRef):
        typeref = ac.annotation.__forward_arg__

    module = sys.modules[ac.class_annotation_was_on.__module__]

    if isinstance(typeref, str):
        if hasattr(module, typeref):
            return getattr(module, typeref)
        elif typeref in __builtins__:
            return __builtins__[typeref]
        else:
            raise NameError("name '{}' is not defined in '{}'".format(
                typeref, module.__name__
            ))
    else:
        return typeref