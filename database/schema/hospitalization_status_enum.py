"""
This module defines the enum for hospitalization status, 
used to describe the condition of an individual at the time 
their sample was collected.
"""
from enum import Enum
from sqlalchemy import Enum as SQLEnum

class HospitalizationStatusEnum(str, Enum):
    AMBULANT = "ambulant"
    HOSPITALIZED = "hospitalized"
    EMERGENCY_ROOM = "emergency room"
    DISCHARGED = "discharged"
    STANDARD_CARE_UNIT = "standard care unit"
    INTENSIVE_CARE_UNIT = "intensive care unit"
    OPERATION_ROOM = "operation room"

hospitalization_status_enum = SQLEnum(
    HospitalizationStatusEnum,
    name="hospitalization_status_enum",
    create_type=True
)
