"""
This module defines the enum for mass units, 
used to describe the amount of DNA in a sample.
"""
from enum import Enum
from sqlalchemy import Enum as SQLEnum

class MassUnitEnum(str, Enum):
    PICOGRAM = "pg"
    NANOGRAM = "ng"
    MICROGRAM = "µg"

mass_unit_enum = SQLEnum(MassUnitEnum, name="mass_unit_enum", create_type=True)
