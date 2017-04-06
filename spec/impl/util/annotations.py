from typing import Any, Dict

from spec.impl.util.typevars import extract_typevars

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


def extract_annotations(cls: type) -> Dict[str, AnnotationContext]:
    real_annotations = {}  # type: Dict[str,AnnotationContext]

    typevars = extract_typevars(cls)

    for klass in cls.mro():
        for attr, annotation in getattr(klass, "__annotations__", {}).items():
            if attr in real_annotations:
                if real_annotations[attr].annotation != annotation:
                    continue
            real_annotations[attr] = AnnotationContext(annotation, klass, typevars)

    return real_annotations