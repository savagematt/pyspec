from typing import Callable

from spec.core import conform, explain_data, equal_to, any_, is_instance, even, odd, is_none, specize, coerce, \
    in_range, gt, lt, lte, gte, describe, is_in, assert_spec, isinvalid, isvalid, coll_of
from spec.impl.core import path, Problem, Explanation, SpecError
from tests.spec.support import check_spec


def test_any():
    s = any_()

    check_spec(s, 1)
    check_spec(s, None)
    check_spec(s, "")


def test_equal_to():
    s = equal_to(1)

    check_spec(s, 1)
    check_spec(s, 2,
               [Problem(path(), 2, s, "expected 1 (int) but got 2 (int)")])


def test_is_instance():
    s = is_instance(int)

    check_spec(s, 1)
    check_spec(s, "",
               [Problem(path(), "", s, "expected an int but got a str")])

    assert is_instance(int) == is_instance(int)


def test_types_as_specs():
    s = int

    check_spec(s, 1)
    check_spec(s, "",
               [Problem(path(), "", is_instance(s), "expected an int but got a str")])


def test_even():
    s = even()

    check_spec(s, 2)
    check_spec(s, 3,
               [Problem(path(), 3, s, "not an even number")])
    check_spec(s, "",
               [Problem(path(), "", s, "not an even number")])


def test_odd():
    s = odd()

    check_spec(s, 3)
    check_spec(s, 4,
               [Problem(path(), 4, s, "not an odd number")])
    check_spec(s, "",
               [Problem(path(), "", s, "not an odd number")])


def test_is_none():
    s = is_none()

    check_spec(s, None)
    check_spec(s, "",
               [Problem(path(), "", s, "not None")])
    check_spec(s, [],
               [Problem(path(), [], s, "not None")])


def test_in_range():
    s = in_range(2, 4)

    check_spec(s, 2)
    check_spec(s, 3)
    check_spec(s, 1,
               [Problem(path(), 1, s, "not between 2 and 4")])
    check_spec(s, 4,
               [Problem(path(), 4, s, "not between 2 and 4")])


def test_greater_than():
    s = gt(2)

    check_spec(s, 3)
    check_spec(s, 2,
               [Problem(path(), 2, s, "not greater than 2")])
    check_spec(s, 1,
               [Problem(path(), 1, s, "not greater than 2")])


def test_less_than():
    s = lt(2)

    check_spec(s, 1)
    check_spec(s, 2,
               [Problem(path(), 2, s, "not less than 2")])
    check_spec(s, 3,
               [Problem(path(), 3, s, "not less than 2")])


def test_less_than_or_equal_to():
    s = lte(2)

    check_spec(s, 1)
    check_spec(s, 2)
    check_spec(s, 3,
               [Problem(path(), 3, s, "not less than or equal to 2")])
    check_spec(s, 4,
               [Problem(path(), 4, s, "not less than or equal to 2")])


def test_greater_than_or_equal_to():
    s = gte(2)

    check_spec(s, 3)
    check_spec(s, 2)
    check_spec(s, 1,
               [Problem(path(), 1, s, "not greater than or equal to 2")])
    check_spec(s, 0,
               [Problem(path(), 0, s, "not greater than or equal to 2")])


def test_specizing_builtin():
    s = callable

    check_spec(s, lambda x: x)

    assert isinvalid(conform(s, "not callable"))

    explanation = explain_data(s, "clearly-not-callable")
    assert explanation is not None
    assert explanation.problems[0].reason == "not callable"
    assert explanation.problems[0].value == "clearly-not-callable"
    assert explanation.problems[0].path == path()


def test_specizing_lambda():
    s = (lambda x: bool(x))

    check_spec(s, True)

    assert isinvalid(conform(s, False))

    explanation = explain_data(s, False)
    assert explanation is not None
    # This is obviously not ideal
    assert explanation.problems[0].reason == "not <lambda>"
    assert explanation.problems[0].value is False
    assert explanation.problems[0].path == path()


def test_specizing_arity_1_lambdas():
    # arity 1 functions are fine
    check_spec(lambda x: True, True)

    # additional varargs should also work
    check_spec(lambda x, *ys: True, True)

    # only varargs should also be fine
    check_spec(lambda *xs: True, True)

    # extra arguments with defaults shouldn't count
    check_spec(lambda x, y=1: True, True)

    # only arguments with defaults should work too
    check_spec(lambda x=1: True, True)
    check_spec(lambda x=1, *xs, **kws: True, True)

    # just trying to break it now
    check_spec(lambda x, y=1, z=2, *xs, **kws: True, True)
    check_spec(lambda x, *xs, **kws: True, True)


def expect_arity_error(c: Callable):
    expected_error_message = 'Expected arity 1 callable as check but got {}'.format(c)
    try:
        # noinspection PyTypeChecker
        conform(c, True)
        assert False, "expected exception during conform"
    except TypeError as e:
        assert expected_error_message in str(e), "checking conform"

    try:
        # noinspection PyTypeChecker
        explain_data(c, True)
        assert False, "expected exception during explain"
    except TypeError as e:
        assert expected_error_message in str(e), "checking explain"

    try:
        # noinspection PyTypeChecker
        describe(c)
        assert False, "expected exception during describe"
    except TypeError as e:
        assert expected_error_message in str(e), "checking describe"


def test_specizing_non_arity_1_lambdas():
    expect_arity_error(lambda x, y: True)
    expect_arity_error(lambda x, y, *varargs: True)
    expect_arity_error(lambda x, y, **kwargs: True)
    expect_arity_error(lambda **kwargs: True)
    expect_arity_error(lambda x, y, *varargs, **kwargs: True)


def test_specizing_callable_objects():
    class ArityOneCallableObject:
        def __call__(self, x: object) -> bool:
            return bool(x)

    assert isvalid(conform(ArityOneCallableObject(), True))
    assert isinvalid(conform(ArityOneCallableObject(), False))

    class DefaultArgsCallableObject:
        def __call__(self, x: object = True, y=False) -> bool:
            return bool(x)

    assert isvalid(conform(DefaultArgsCallableObject(), True))
    assert isinvalid(conform(DefaultArgsCallableObject(), False))


def test_sets():
    s = {"a", "b"}

    check_spec(s, "a")
    check_spec(s, "b")
    check_spec(s, "c",
               [Problem(path(), "c", specize(s), "not in ['a', 'b']")])


def test_is_in_over_sets():
    s = is_in({"a", "b"})

    check_spec(s, "a")
    check_spec(s, "b")
    check_spec(s, "c",
               [Problem(path(), "c", specize(s), "not in ['a', 'b']")])


def test_is_in_over_dicts():
    s = is_in({"a": 1, "b": 2})

    check_spec(s, "a")
    check_spec(s, "b")
    check_spec(s, "c",
               [Problem(path(), "c", specize(s), "not in ['a', 'b']")])


def test_is_in_over_lists():
    s = is_in(["a", "b"])

    check_spec(s, "a")
    check_spec(s, "b")
    check_spec(s, "c",
               [Problem(path(), "c", specize(s), "not in ['a', 'b']")])


class CoercingClass:
    def __call__(self, x):
        return int(x)


def test_coerce():
    underlying_spec = in_range(1, 2)
    s = coerce(int, underlying_spec)

    check_spec(s, 1)
    check_spec(s, "1", expected_conform=1)

    # TODO: problem contains underlying_spec. Not sure yet if this is the right behaviour
    check_spec(s, 2, [Problem(path(), 2, underlying_spec, "not between 1 and 2")])
    check_spec(s, "2", [Problem(path(), 2, underlying_spec, "not between 1 and 2")])

    check_spec(s, "one",
               [Problem(path(), "one", s,
                        "could not coerce 'one' (str) using coercer: int because:\n"
                        "invalid literal for int() with base 10: 'one'")])

    spec_using_a_class_as_a_coercer = coerce(CoercingClass(), underlying_spec)
    check_spec(spec_using_a_class_as_a_coercer, "one",
               [Problem(path(),
                        "one",
                        spec_using_a_class_as_a_coercer,
                        "could not coerce 'one' (str) using coercer: CoercingClass because:\n"
                        "invalid literal for int() with base 10: 'one'")])

    spec_using_a_lambda_as_a_coercer = coerce(lambda x: int(x), underlying_spec)
    check_spec(spec_using_a_lambda_as_a_coercer, "one",
               [Problem(path(), "one", spec_using_a_lambda_as_a_coercer,
                        "could not coerce 'one' (str) using coercer: <lambda> because:\n"
                        "invalid literal for int() with base 10: 'one'")])


def test_assert():
    s = specize(int)

    assert_spec(s, 1)

    try:
        assert_spec(s, "one")
        assert False, "Expected exception"
    except SpecError as e:
        error = e

    assert error.explanation == Explanation.with_problems(Problem(path(), "one", s, "expected an int but got a str"))


def test_coll_of():
    item_spec = specize(int)
    s = coll_of(item_spec)

    check_spec(s, [1])
    check_spec(s, [1, 2])
    check_spec(s, (1, 2))

    try:
        assert_spec(s, ["one", 2, "three"])
        assert False, "Expected exception"
    except SpecError as e:
        error = e
        assert error.explanation == Explanation.with_problems(
            Problem(path(0), "one", item_spec, "expected an int but got a str"),
            Problem(path(2), "three", item_spec, "expected an int but got a str"))

    try:
        assert_spec(s, 1)
        assert False, "Expected exception"
    except SpecError as e:
        error = e
        assert error.explanation == Explanation.with_problems(Problem(path(), 1, s, "not iterable"))
