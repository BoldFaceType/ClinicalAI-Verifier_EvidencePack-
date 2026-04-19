from __future__ import annotations

from dataclasses import dataclass

try:
    from pydantic import BaseModel, ConfigDict, field_validator
except ImportError:
    BaseModel = None
    ConfigDict = None
    field_validator = None


REQUIRED_FIELDS = (
    "member_id",
    "measure_id",
    "screening_date",
    "screening_tool",
    "screening_score",
    "screening_loinc",
    "bipolar_history",
    "prior_year_depression_dx",
    "source_kind",
)

ALL_FIELDS = REQUIRED_FIELDS + (
    "follow_up_code",
    "follow_up_date",
    "measure_year",
)

MEASURE_ID = "DSF-E"

APPROVED_LOINC_BY_TOOL: dict[str, set[str]] = {
    "PHQ-2": {"44249-1"},
    "PHQ-9": {"44261-6"},
}

# Reverse map: LOINC code → screening tool name
LOINC_TO_TOOL: dict[str, str] = {
    loinc: tool
    for tool, loincs in APPROVED_LOINC_BY_TOOL.items()
    for loinc in loincs
}

FOLLOW_UP_CODES = {"96127", "G8431", "G8510", "99484"}
THRESHOLDS = {"PHQ-2": 3, "PHQ-9": 10}
BOOLEAN_TRUE = {"1", "true", "yes", "y"}
BOOLEAN_FALSE = {"0", "false", "no", "n"}
VALID_SOURCE_KINDS: frozenset[str] = frozenset({"structured"})


if BaseModel is not None:

    class DsfeRowModel(BaseModel):
        model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

        member_id: str = ""
        measure_id: str = ""
        screening_date: str = ""
        screening_tool: str = ""
        screening_score: str = ""
        screening_loinc: str = ""
        follow_up_code: str = ""
        follow_up_date: str = ""
        bipolar_history: str = ""
        prior_year_depression_dx: str = ""
        source_kind: str = ""
        measure_year: str = ""

        @field_validator("*", mode="before")
        @classmethod
        def normalize_value(cls, value: object) -> str:
            return str(value or "").strip()
else:
    DsfeRowModel = None


@dataclass(frozen=True)
class DsfeRecord:
    member_id: str
    measure_id: str
    screening_date: str
    screening_tool: str
    screening_score: str
    screening_loinc: str
    follow_up_code: str
    follow_up_date: str
    bipolar_history: str
    prior_year_depression_dx: str
    source_kind: str
    measure_year: str
    input_format: str
    row_number: int

    @classmethod
    def from_mapping(
        cls, row: dict[str, object], *, input_format: str, row_number: int
    ) -> "DsfeRecord":
        if DsfeRowModel is not None:
            normalized = DsfeRowModel.model_validate(row).model_dump()
        else:
            normalized = {field: str(row.get(field, "") or "").strip() for field in ALL_FIELDS}
        return cls(**normalized, input_format=input_format, row_number=row_number)
