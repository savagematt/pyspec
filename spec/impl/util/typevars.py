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