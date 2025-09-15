"""
This module defines the enum for volume units, 
used to describe the volume of a carrying liquid in a sample.
"""
from enum import Enum
from sqlalchemy import Enum as SQLEnum

class VolumeUnitEnum(str, Enum):
    MICROLITER = "µL"
    MILLILITER = "mL"
    LITER = "L"

volume_unit_enum = SQLEnum(
    VolumeUnitEnum,
    name="volume_unit_enum",
    create_type=True
)
