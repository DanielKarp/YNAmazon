"""Provides utilities for handling missing values using enums.

See: https://peps.python.org/pep-0484/#support-for-singleton-types-in-unions

Classes:
    Missing (enum.Enum): An enumeration to represent a missing value token.

Constants:
    MISSING (Missing): A constant representing the missing value token from the Missing enum.

__all__:
    List of public objects of this module, as interpreted by import *.

"""

from enum import Enum


class Missing(Enum):
    token = 0


MISSING = Missing.token
