from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from preflight_validator.schemas.dsfe import (
    APPROVED_LOINC_BY_TOOL,
    BOOLEAN_FALSE,
    BOOLEAN_TRUE,
    FOLLOW_UP_CODES,
    REQUIRED_FIELDS,
    THRESHOLDS,
    DsfeRecord,
)


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    severity: str
    member_id: str
    field: str
    message: str
    stage: str
    row_number: int


def run_rules(records: list[DsfeRecord]) -> list[RuleResult]:
    findings: list[RuleResult] = []
    for record in records:
        findings.extend(_file_format_validation(record))
        findings.extend(_data_structure_validation(record))
        findings.extend(_value_set_validation(record))
        findings.extend(_threshold_logic_validation(record))
        findings.extend(_follow_up_validation(record))
        findings.extend(_exclusion_validation(record))
    return findings


def _file_format_validation(record: DsfeRecord) -> Iterable[RuleResult]:
    for field in REQUIRED_FIELDS:
        if not getattr(record, field):
            yield RuleResult(
                rule_id=f"FR1_MISSING_{field.upper()}",
                severity="ERROR",
                member_id=record.member_id,
                field=field,
                message=f"{field} is required.",
                stage="file_format_validation",
                row_number=record.row_number,
            )


def _data_structure_validation(record: DsfeRecord) -> Iterable[RuleResult]:
    if record.measure_id and record.measure_id != "DSF-E":
        yield _result(
            record,
            "FR2_INVALID_MEASURE_ID",
            "measure_id",
            "measure_id must be DSF-E.",
            "data_structure_validation",
        )
    if record.screening_tool and record.screening_tool not in THRESHOLDS:
        yield _result(
            record,
            "FR2_UNSUPPORTED_SCREENING_TOOL",
            "screening_tool",
            "screening_tool must be one of PHQ-2 or PHQ-9.",
            "data_structure_validation",
        )
    if record.source_kind and record.source_kind.lower() != "structured":
        yield _result(
            record,
            "FR2_NON_STRUCTURED_CAPTURE",
            "source_kind",
            "Screening results must be captured as structured discrete values.",
            "data_structure_validation",
        )
    if record.screening_score:
        if not _is_number(record.screening_score):
            yield _result(
                record,
                "FR2_NON_NUMERIC_SCREENING_SCORE",
                "screening_score",
                "screening_score must be numeric.",
                "data_structure_validation",
            )
        elif "." in record.screening_score:
            yield _result(
                record,
                "FR2_NON_DISCRETE_SCREENING_SCORE",
                "screening_score",
                "screening_score must be a discrete numeric value.",
                "data_structure_validation",
            )


def _value_set_validation(record: DsfeRecord) -> Iterable[RuleResult]:
    approved_loinc = APPROVED_LOINC_BY_TOOL.get(record.screening_tool)
    if record.screening_tool and approved_loinc and record.screening_loinc not in approved_loinc:
        yield _result(
            record,
            "FR3_INVALID_LOINC",
            "screening_loinc",
            f"screening_loinc must match the approved DSF-E value set for {record.screening_tool}.",
            "value_set_validation",
        )


def _threshold_logic_validation(record: DsfeRecord) -> Iterable[RuleResult]:
    if not record.screening_tool or not _is_number(record.screening_score):
        return
    threshold = THRESHOLDS[record.screening_tool]
    score = int(float(record.screening_score))
    if score >= threshold and not record.follow_up_code:
        yield _result(
            record,
            "FR4_POSITIVE_SCREEN_MISSING_FOLLOW_UP_CODE",
            "follow_up_code",
            f"{record.screening_tool} scores meeting the threshold require a qualifying follow-up code.",
            "threshold_logic_validation",
        )


def _follow_up_validation(record: DsfeRecord) -> Iterable[RuleResult]:
    if not record.follow_up_code and not record.follow_up_date:
        return
    if record.follow_up_code and record.follow_up_code not in FOLLOW_UP_CODES:
        yield _result(
            record,
            "FR5_INVALID_FOLLOW_UP_CODE",
            "follow_up_code",
            "follow_up_code must be a qualifying DSF-E CPT/HCPCS code.",
            "follow_up_validation",
        )
    screening_date = _parse_iso_date(record.screening_date)
    follow_up_date = _parse_iso_date(record.follow_up_date)
    if record.follow_up_date and follow_up_date is None:
        yield _result(
            record,
            "FR5_INVALID_FOLLOW_UP_DATE",
            "follow_up_date",
            "follow_up_date must use YYYY-MM-DD format.",
            "follow_up_validation",
        )
        return
    if screening_date is None:
        if record.screening_date:
            yield _result(
                record,
                "FR5_INVALID_SCREENING_DATE",
                "screening_date",
                "screening_date must use YYYY-MM-DD format.",
                "follow_up_validation",
            )
        return
    if follow_up_date and follow_up_date < screening_date:
        yield _result(
            record,
            "FR5_FOLLOW_UP_BEFORE_SCREENING",
            "follow_up_date",
            "follow_up_date cannot be earlier than screening_date.",
            "follow_up_validation",
        )
    elif follow_up_date and (follow_up_date - screening_date).days > 30:
        yield _result(
            record,
            "FR5_FOLLOW_UP_OUTSIDE_WINDOW",
            "follow_up_date",
            "follow-up must occur within 30 days of the screening.",
            "follow_up_validation",
        )


def _exclusion_validation(record: DsfeRecord) -> Iterable[RuleResult]:
    bipolar = _parse_boolean(record.bipolar_history)
    prior_year_depression = _parse_boolean(record.prior_year_depression_dx)
    if bipolar is None and record.bipolar_history:
        yield _result(
            record,
            "FR6_INVALID_BIPOLAR_HISTORY_FLAG",
            "bipolar_history",
            "bipolar_history must be a boolean-like value.",
            "exclusion_validation",
        )
    if prior_year_depression is None and record.prior_year_depression_dx:
        yield _result(
            record,
            "FR6_INVALID_PRIOR_YEAR_DEPRESSION_FLAG",
            "prior_year_depression_dx",
            "prior_year_depression_dx must be a boolean-like value.",
            "exclusion_validation",
        )
    if bipolar is True:
        yield _result(
            record,
            "FR6_MEMBER_EXCLUDED_BIPOLAR_HISTORY",
            "bipolar_history",
            "Member is excluded from DSF-E due to bipolar disorder history.",
            "exclusion_validation",
            severity="WARN",
        )
    if prior_year_depression is True:
        yield _result(
            record,
            "FR6_MEMBER_EXCLUDED_PRIOR_DEPRESSION",
            "prior_year_depression_dx",
            "Member is excluded from DSF-E due to prior-year depression diagnosis.",
            "exclusion_validation",
            severity="WARN",
        )


def _result(
    record: DsfeRecord,
    rule_id: str,
    field: str,
    message: str,
    stage: str,
    *,
    severity: str = "ERROR",
) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        severity=severity,
        member_id=record.member_id,
        field=field,
        message=message,
        stage=stage,
        row_number=record.row_number,
    )


def _parse_iso_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _parse_boolean(value: str) -> bool | None:
    normalized = value.strip().lower()
    if not normalized:
        return False
    if normalized in BOOLEAN_TRUE:
        return True
    if normalized in BOOLEAN_FALSE:
        return False
    return None
