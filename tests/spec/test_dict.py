from uuid import UUID

import spec.coercions as sc
from spec.core import equal_to, in_range, dict_spec, dict_example
from spec.impl.core import Problem, path
from tests.spec.support import check_spec


def test_dict_example_treats_values_as_equal_to_spec():
    expected_value = UUID('80b71e04-9862-462b-ac0c-0c34dc272c7b')

    s = dict_example({'k': expected_value})

    check_spec(s, {'k': expected_value})

    wrong_value = UUID('a5bef1a0-d139-49d3-91ff-79a69aa39759')
    check_spec(s, {'k': wrong_value},
               [Problem(path('k'), wrong_value, equal_to(expected_value),
                        "expected 80b71e04-9862-462b-ac0c-0c34dc272c7b (UUID) but got a5bef1a0-d139-49d3-91ff-79a69aa39759 (UUID)")])


def test_dict_example_treats_dict_values_as_more_dict_examples():
    expected_value = UUID('80b71e04-9862-462b-ac0c-0c34dc272c7b')

    s = dict_example({'j': {'k': expected_value}})

    check_spec(s, {'j': {'k': expected_value}})

    wrong_value = UUID('a5bef1a0-d139-49d3-91ff-79a69aa39759')
    check_spec(s, {'j': {'k': wrong_value}},
               [Problem(path('j', 'k'), wrong_value, equal_to(expected_value),
                        "expected 80b71e04-9862-462b-ac0c-0c34dc272c7b (UUID) but got a5bef1a0-d139-49d3-91ff-79a69aa39759 (UUID)")])


def test_dict_spec_returns_conformed_values():
    s = dict_spec({'k': sc.Uuid})

    expected_conformed_value = UUID('80b71e04-9862-462b-ac0c-0c34dc272c7b')
    original_value = str(expected_conformed_value)

    check_spec(s, {'k': original_value}, expected_conform={'k': expected_conformed_value})