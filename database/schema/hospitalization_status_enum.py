"""
This module defines the enum for hospitalization status, 
used to describe the condition of an individual at the time 
their sample was collected.
"""
from enum import Enum
from sqlalchemy import Enum as SQLEnum

class HospitalizationStatusEnum(str, Enum):
    AMBULANT = "Ambulant"
    HOSPITALIZED = "Hospitalized"
    EMERGENCY_ROOM = "Emergency room"
    DISCHARGED = "Discharged"
    STANDARD_CARE_UNIT = "Standard care unit"
    INTENSIVE_CARE_UNIT = "Intensive care unit"
    OPERATION_ROOM = "Operation room"

hospitalization_status_enum = SQLEnum(
    HospitalizationStatusEnum,
    name="hospitalization_status_enum",
    create_type=True
)
