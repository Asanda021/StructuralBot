"""
StructuralBot - Iran Design Codes

Iranian structural design code implementations.

This package contains:
- Material rules
- Concrete design rules
- Reinforcement rules
- Detailing rules

The exact code edition must always be explicitly selected.
"""

from codes.iran.materials import IranMaterials
from codes.iran.concrete import IranConcrete
from codes.iran.reinforcement import IranReinforcement
from codes.iran.detailing import IranDetailing


__all__ = [
    "IranMaterials",
    "IranConcrete",
    "IranReinforcement",
    "IranDetailing",
]
