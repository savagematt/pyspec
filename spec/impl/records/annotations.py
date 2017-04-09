from typing import Any, Dict, _ForwardRef

from spec.impl.records.typevars import generic_class_typevars

Hint = Any


class AnnotationContext:
    annotation: Hint
    class_annotation_was_on: type
    typevars_from_class: Dict[str, Hint]

    def __init__(self,
                 annotation: Hint,
                 klass: type,
                 typevars: Dict[str, Hint]):
        self.annotation = annotation
        self.class_annotation_was_on = klass
        self.typevars_from_class = typevars

    def for_hint(self, hint: Hint) -> 'AnnotationContext':
        return AnnotationContext(hint, self.class_annotation_was_on, self.typevars_from_class)


def extract_annotations(cls: type) -> Dict[str, AnnotationContext]:
    real_annotations = {}  # type: Dict[str,AnnotationContext]

    typevars = generic_class_typevars(cls)

    for klass in cls.mro():
        for attr, annotation in getattr(klass, "__annotations__", {}).items():
            if attr in real_annotations:
                if real_annotations[attr].annotation != annotation:
                    continue
            real_annotations[attr] = AnnotationContext(annotation, klass, typevars)

    return real_annotations
