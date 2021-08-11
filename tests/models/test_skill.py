from unittest.mock import Mock

import pytest

from backend.models.skill import SkillWithoutLevelMixin, SkillWithLevelMixin


def __skill_without_level(request):
    class MockSkillWithoutLevel(SkillWithoutLevelMixin):
        # Redefine skill instead of patching just to suppress SQLAlchemy warning:
        # 'Unmanaged access of declarative attribute skill from non-mapped class ...'
        @property
        def skill(self):
            return Mock(id=request.param)
    return MockSkillWithoutLevel()


def __skill_with_level(request):
    class MockSkillWithLevel(SkillWithLevelMixin):
        def __init__(self):
            self.level = request.param[1]

        # Redefine skill instead of patching just to suppress SQLAlchemy warning:
        # 'Unmanaged access of declarative attribute skill from non-mapped class ...'
        @property
        def skill(self):
            return Mock(id=request.param[0])
    return MockSkillWithLevel()


fixture_skill_without_level = pytest.fixture(__skill_without_level, name='skill_without_level')
fixture_other_skill_without_level = pytest.fixture(__skill_without_level, name='other_skill_without_level')

fixture_skill_with_level = pytest.fixture(__skill_with_level, name='skill_with_level')
fixture_other_skill_with_level = pytest.fixture(__skill_with_level, name='other_skill_with_level')


TEST_DATA = {
    'test_skill_without_level_matching': [
        ('skill_id_match', (1, 1, True)),
        ('skill_id_mismatch', (1, 2, False)),
    ],
    'test_skill_with_level_matching': [
        ('skill_id_match_level_higher', ((1, 55), (1, 75), True)),
        ('skill_id_match_level_match', ((1, 55), (1, 55), True)),
        ('skill_id_match_level_lower_in_range', ((1, 55), (1, 45), True)),
        ('skill_id_match_level_lower_outside_range', ((1, 55), (1, 25), False)),
        ('skill_id_mismatch_level_higher', ((1, 55), (2, 75), False)),
        ('skill_id_mismatch_level_match', ((1, 55), (2, 55), False)),
        ('skill_id_mismatch_level_lower_in_range', ((1, 55), (2, 45), False)),
        ('skill_id_mismatch_level_lower_outside_range', ((1, 55), (2, 25), False)),
    ],
    'test_skill_without_level_matching_skill_with_level': [
        ('skill_id_match', (1, (1, 75), True)),
        ('skill_id_mismatch', (1, (2, 75), False)),
    ],
    'test_skill_with_level_matching_skill_without_level': [
        ('skill_id_match', ((1, 75), 1, False)),
        ('skill_id_mismatch', ((1, 75), 2, False)),
    ]
}


def parametrize_with_test_data(func):
    # inspect the function code and extract all the parameter names
    argnames = func.__code__.co_varnames[:func.__code__.co_argcount]

    # apply 'indirect' on all args except 'expected'
    indirect = [name for name in argnames if name != 'expected']

    # get the test data and ids using the function name
    argvalues = [data for _, data in TEST_DATA[func.__name__]]
    ids = [test_id for test_id, _ in TEST_DATA[func.__name__]]
    return pytest.mark.parametrize(argnames, argvalues, indirect=indirect, ids=ids)(func)


@parametrize_with_test_data
def test_skill_without_level_matching(skill_without_level, other_skill_without_level, expected):
    assert skill_without_level.matches(other_skill_without_level) == expected


@parametrize_with_test_data
def test_skill_with_level_matching(skill_with_level, other_skill_with_level, expected):
    assert skill_with_level.matches(other_skill_with_level) == expected


@parametrize_with_test_data
def test_skill_without_level_matching_skill_with_level(skill_without_level, skill_with_level, expected):
    assert skill_without_level.matches(skill_with_level) == expected


@parametrize_with_test_data
def test_skill_with_level_matching_skill_without_level(skill_with_level, skill_without_level, expected):
    assert skill_with_level.matches(skill_without_level) == expected
