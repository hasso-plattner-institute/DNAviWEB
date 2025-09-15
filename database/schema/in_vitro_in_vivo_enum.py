"""
This module defines the enum to describe if
a sample was in vivo or in vitro.
"""
from enum import Enum
from sqlalchemy import Enum as SQLEnum

class InVitroInVivoEnum(str, Enum):
    IN_VITRO = "in_vitro"
    IN_VIVO = "in_vivo"

in_vitro_in_vivo_enum = SQLEnum(
    InVitroInVivoEnum,
    name="in_vitro_in_vivo_enum",
    create_type=True 
)
