from typing import Optional, Iterable

from spec.core import conform, explain_data, INVALID, specize, Speccable
from spec.impl.core import Problem, path, Explanation

UNDEFINED = object()


def check_spec(s: Speccable,
               value: object,
               expected_problems: Optional[Iterable[Problem]] = None,
               expected_conform: object = UNDEFINED):
    """
    Always adds path("inserted_by_check_spec") to explain() call, to ensure paths appear in problems correctly
    """

    if expected_problems:
        expected_explanation = Explanation.with_problems(*expected_problems)
        if expected_conform != UNDEFINED:
            raise ValueError("Conform should always be INVALID if explain() is invalid")
        expected_conform = INVALID
    else:
        expected_problems = []
        expected_explanation = None

    if expected_conform == UNDEFINED:
        expected_conform = value

    assert explain_data(s, value) == expected_explanation, "\nexpected:\n{}\n\nbut was:\n{}".format(
        str(expected_explanation), str(explain_data(s, value)))

    assert conform(s, value) == expected_conform, "\nexpected:\n{}\n\nbut was:\n{}".format(str(expected_conform),
                                                                                           str(conform(s, value)))

    path_element = "added_by_check_spec"
    problems_which_should_include_path = specize(s).explain(path(path_element), value)
    for p in problems_which_should_include_path:
        assert len(p.path) >= 1 and p.path[0] == path_element, \
            "spec {} might not be extending paths correctly in explain".format(type(s))
