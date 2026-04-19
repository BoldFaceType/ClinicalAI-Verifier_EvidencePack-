"""
DSF-E validation rule engine.

Schema version  : dsfe-v0.2
Validator version: 0.2.0
Updated          : 2026-04-01

Rule inventory
--------------
Stage 1  - file_format_validation
  FR1_MISSING_<FIELD>         ERROR  Required field absent or empty

Stage 2  - data_structure_validation
  FR2_INVALID_MEASURE_ID              ERROR  measure_id != "DSF-E"
  FR2_UNSUPPORTED_SCREENING_TOOL      ERROR  tool not in {PHQ-2, PHQ-9}
  FR2_NON_STRUCTURED_CAPTURE          ERROR  source_kind != "structured"
  FR2_NON_NUMERIC_SCREENING_SCORE     ERROR  score is not numeric
  FR2_NON_DISCRETE_SCREENING_SCORE    ERROR  score contains decimal point
  FR2_INVALID_SCREENING_DATE_FORMAT   ERROR  screening_date not YYYY-MM-DD (NEW v0.2)
  FR2_INVALID_MEASURE_YEAR_FORMAT     WARN   measure_year present but not 4-digit YYYY (NEW v0.2)

Stage 3  - value_set_validation
  FR3_INVALID_LOINC                   ERROR  LOINC code not in approved set for tool
  FR3_LOINC_TOOL_MISMATCH             ERROR  LOINC maps to a different tool (NEW v0.2)

Stage 4  - threshold_logic_validation
  FR4_POSITIVE_SCREEN_MISSING_FOLLOW_UP_CODE  ERROR  score >= threshold but no follow-up code

Stage 5  - follow_up_validation
  FR5_INVALID_FOLLOW_UP_CODE          ERROR  follow_up_code not in approved CPT/HCPCS set
  FR5_INVALID_FOLLOW_UP_DATE          ERROR  follow_up_date not YYYY-MM-DD
  FR5_INVALID_SCREENING_DATE          ERROR  screening_date not parseable when follow-up present
  FR5_FOLLOW_UP_BEFORE_SCREENING      ERROR  follow_up_date < screening_date
  FR5_FOLLOW_UP_OUTSIDE_WINDOW        ERROR  follow-up > 30 days after screening

Stage 6  - exclusion_validation
  FR6_INVALID_BIPOLAR_HISTORY_FLAG       ERROR  bipolar_history not boolean-like
  FR6_INVALID_PRIOR_YEAR_DEPRESSION_FLAG ERROR  prior_year_depression_dx not boolean-like
  FR6_MEMBER_EXCLUDED_BIPOLAR_HISTORY    WARN   member has bipolar history
  FR6_MEMBER_EXCLUDED_PRIOR_DEPRESSION   WARN   member has prior-year depression dx
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from preflight_validator.schemas.dsfe import (
    APPROVED_LOINC_BY_TOOL,
    BOOLEAN_FALSE,
    BOOLEAN_TRUE,
    FOLLOW_UP_CODES,
    LOINC_TO_TOOL,
    MEASURE_ID,
    REQUIRED_FIELDS,
    THRESHOLDS,
    VALID_SOURCE_KINDS,
    DsfeRecord,
)

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_YEAR_RE = re.compile(r"^\d{4}$")


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
    for field_name in REQUIRED_FIELDS:
        if not getattr(record, field_name):
            yield RuleResult(
                rule_id=f"FR1_MISSING_{field_name.upper()}",
                severity="ERROR",
                member_id=record.member_id,
                field=field_name,
                message=f"{field_name} is required and must not be empty.",
                stage="file_format_validation",
                row_number=record.row_number,
            )


def _data_structure_validation(record: DsfeRecord) -> Iterable[RuleResult]:
    if record.measure_id and record.measure_id != MEASURE_ID:
        yield _result(record, "FR2_INVALID_MEASURE_ID", "measure_id",
                      f"measure_id must be '{MEASURE_ID}'. Received: '{record.measure_id}'.",
                      "data_structure_validation")
    if record.screening_tool and record.screening_tool not in THRESHOLDS:
        yield _result(record, "FR2_UNSUPPORTED_SCREENING_TOOL", "screening_tool",
                      f"screening_tool must be one of {sorted(THRESHOLDS)}. "
                      f"Received: '{record.screening_tool}'.",
                      "data_structure_validation")
    if record.source_kind and record.source_kind.lower() not in VALID_SOURCE_KINDS:
        yield _result(record, "FR2_NON_STRUCTURED_CAPTURE", "source_kind",
                      f"source_kind must be 'structured'. Received: '{record.source_kind}'.",
                      "data_structure_validation")
    if record.screening_score:
        if not _is_number(record.screening_score):
            yield _result(record, "FR2_NON_NUMERIC_SCREENING_SCORE", "screening_score",
                          f"screening_score must be numeric. Received: '{record.screening_score}'.",
                          "data_structure_validation")
        elif "." in record.screening_score:
            yield _result(record, "FR2_NON_DISCRETE_SCREENING_SCORE", "screening_score",
                          f"screening_score must be an integer. Received: '{record.screening_score}'.",
                          "data_structure_validation")
    # NEW v0.2
    if record.screening_date and not _ISO_DATE_RE.match(record.screening_date):
        yield _result(record, "FR2_INVALID_SCREENING_DATE_FORMAT", "screening_date",
                      f"screening_date must use YYYY-MM-DD format. Received: '{record.screening_date}'.",
                      "data_structure_validation")
    if record.measure_year and not _YEAR_RE.match(record.measure_year):
        yield _result(record, "FR2_INVALID_MEASURE_YEAR_FORMAT", "measure_year",
                      f"measure_year should be a 4-digit year. Received: '{record.measure_year}'.",
                      "data_structure_validation", severity="WARN")


def _value_set_validation(record: DsfeRecord) -> Iterable[RuleResult]:
    approved_loinc = APPROVED_LOINC_BY_TOOL.get(record.screening_tool)
    if record.screening_tool and approved_loinc and record.screening_loinc not in approved_loinc:
        yield _result(record, "FR3_INVALID_LOINC", "screening_loinc",
                      f"screening_loinc '{record.screening_loinc}' not in approved set for "
                      f"{record.screening_tool}. Expected: {sorted(approved_loinc)}.",
                      "value_set_validation")
    elif (record.screening_loinc and record.screening_tool
          and record.screening_loinc in LOINC_TO_TOOL
          and LOINC_TO_TOOL[record.screening_loinc] != record.screening_tool):
        expected = LOINC_TO_TOOL[record.screening_loinc]
        yield _result(record, "FR3_LOINC_TOOL_MISMATCH", "screening_loinc",
                      f"screening_loinc '{record.screening_loinc}' belongs to {expected}, "
                      f"but screening_tool is '{record.screening_tool}'.",
                      "value_set_validation")


def _threshold_logic_validation(record: DsfeRecord) -> Iterable[RuleResult]:
    if not record.screening_tool or not _is_number(record.screening_score):
        return
    threshold = THRESHOLDS.get(record.screening_tool)
    if threshold is None:
        return
    score = int(float(record.screening_score))
    if score >= threshold and not record.follow_up_code:
        yield _result(record, "FR4_POSITIVE_SCREEN_MISSING_FOLLOW_UP_CODE", "follow_up_code",
                      f"{record.screening_tool} score {score} meets threshold ({threshold}). "
                      "A qualifying follow-up code is required.",
                      "threshold_logic_validation")


def _follow_up_validation(record: DsfeRecord) -> Iterable[RuleResult]:
    if not record.follow_up_code and not record.follow_up_date:
        return
    if record.follow_up_code and record.follow_up_code not in FOLLOW_UP_CODES:
        yield _result(record, "FR5_INVALID_FOLLOW_UP_CODE", "follow_up_code",
                      f"follow_up_code '{record.follow_up_code}' is not a qualifying code. "
                      f"Approved: {sorted(FOLLOW_UP_CODES)}.",
                      "follow_up_validation")
    screening_date = _parse_iso_date(record.screening_date)
    follow_up_date = _parse_iso_date(record.follow_up_date)
    if record.follow_up_date and follow_up_date is None:
        yield _result(record, "FR5_INVALID_FOLLOW_UP_DATE", "follow_up_date",
                      f"follow_up_date must use YYYY-MM-DD format. Received: '{record.follow_up_date}'.",
                      "follow_up_validation")
        return
    if screening_date is None:
        if record.screening_date:
            yield _result(record, "FR5_INVALID_SCREENING_DATE", "screening_date",
                          f"screening_date must use YYYY-MM-DD format. Received: '{record.screening_date}'.",
                          "follow_up_validation")
        return
    if follow_up_date and follow_up_date < screening_date:
        yield _result(record, "FR5_FOLLOW_UP_BEFORE_SCREENING", "follow_up_date",
                      f"follow_up_date ({record.follow_up_date}) is before "
                      f"screening_date ({record.screening_date}).",
                      "follow_up_validation")
    elif follow_up_date and (follow_up_date - screening_date).days > 30:
        delta = (follow_up_date - screening_date).days
        yield _result(record, "FR5_FOLLOW_UP_OUTSIDE_WINDOW", "follow_up_date",
                      f"Follow-up must be within 30 days. Gap was {delta} days.",
                      "follow_up_validation")


def _exclusion_validation(record: DsfeRecord) -> Iterable[RuleResult]:
    bipolar = _parse_boolean(record.bipolar_history)
    prior = _parse_boolean(record.prior_year_depression_dx)
    if bipolar is None and record.bipolar_history:
        yield _result(record, "FR6_INVALID_BIPOLAR_HISTORY_FLAG", "bipolar_history",
                      f"bipolar_history must be boolean-like. Received: '{record.bipolar_history}'.",
                      "exclusion_validation")
    if prior is None and record.prior_year_depression_dx:
        yield _result(record, "FR6_INVALID_PRIOR_YEAR_DEPRESSION_FLAG", "prior_year_depression_dx",
                      f"prior_year_depression_dx must be boolean-like. Received: '{record.prior_year_depression_dx}'.",
                      "exclusion_validation")
    if bipolar is True:
        yield _result(record, "FR6_MEMBER_EXCLUDED_BIPOLAR_HISTORY", "bipolar_history",
                      "Member excluded: documented bipolar disorder history.",
                      "exclusion_validation", severity="WARN")
    if prior is True:
        yield _result(record, "FR6_MEMBER_EXCLUDED_PRIOR_DEPRESSION", "prior_year_depression_dx",
                      "Member excluded: prior-year depression diagnosis.",
                      "exclusion_validation", severity="WARN")


def _result(record: DsfeRecord, rule_id: str, field: str, message: str, stage: str,
            *, severity: str = "ERROR") -> RuleResult:
    return RuleResult(rule_id=rule_id, severity=severity, member_id=record.member_id,
                      field=field, message=message, stage=stage, row_number=record.row_number)


def _parse_iso_date(value: str) -> date | None:
    if not value or not _ISO_DATE_RE.match(value):
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
    n = value.strip().lower()
    if not n:
        return False
    if n in BOOLEAN_TRUE:
        return True
    if n in BOOLEAN_FALSE:
        return False
    return None
