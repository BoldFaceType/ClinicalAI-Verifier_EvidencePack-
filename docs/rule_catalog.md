# DSF-E Rule Catalog

This catalog documents the v0.1 DSF-E pre-flight validator findings emitted by `preflight_validator`.

## Stage: File Format Validation

- `FR1_MISSING_MEMBER_ID`: `member_id` is required.
- `FR1_MISSING_MEASURE_ID`: `measure_id` is required.
- `FR1_MISSING_SCREENING_DATE`: `screening_date` is required.
- `FR1_MISSING_SCREENING_TOOL`: `screening_tool` is required.
- `FR1_MISSING_SCREENING_SCORE`: `screening_score` is required.
- `FR1_MISSING_SCREENING_LOINC`: `screening_loinc` is required.
- `FR1_MISSING_BIPOLAR_HISTORY`: `bipolar_history` is required.
- `FR1_MISSING_PRIOR_YEAR_DEPRESSION_DX`: `prior_year_depression_dx` is required.
- `FR1_MISSING_SOURCE_KIND`: `source_kind` is required.

## Stage: Data Structure Validation

- `FR2_INVALID_MEASURE_ID`: `measure_id` must be `DSF-E`.
- `FR2_UNSUPPORTED_SCREENING_TOOL`: `screening_tool` must be `PHQ-2` or `PHQ-9`.
- `FR2_NON_STRUCTURED_CAPTURE`: screening data cannot be free text or note-only capture.
- `FR2_NON_NUMERIC_SCREENING_SCORE`: `screening_score` must parse as numeric.
- `FR2_NON_DISCRETE_SCREENING_SCORE`: `screening_score` must be a discrete numeric value.

## Stage: Value Set Validation

- `FR3_INVALID_LOINC`: `screening_loinc` does not match the approved DSF-E LOINC set for the selected instrument.

## Stage: Threshold Logic Validation

- `FR4_POSITIVE_SCREEN_MISSING_FOLLOW_UP_CODE`: a positive PHQ-2 or PHQ-9 screen is missing a qualifying follow-up code.

Thresholds:

- `PHQ-2 >= 3`
- `PHQ-9 >= 10`

## Stage: Follow-Up Validation

- `FR5_INVALID_FOLLOW_UP_CODE`: `follow_up_code` is not in the qualifying DSF-E follow-up set.
- `FR5_INVALID_FOLLOW_UP_DATE`: `follow_up_date` must be ISO `YYYY-MM-DD`.
- `FR5_INVALID_SCREENING_DATE`: `screening_date` must be ISO `YYYY-MM-DD` when follow-up timing is evaluated.
- `FR5_FOLLOW_UP_BEFORE_SCREENING`: follow-up cannot occur before the screening.
- `FR5_FOLLOW_UP_OUTSIDE_WINDOW`: follow-up must occur within 30 days of the screening.

Qualifying follow-up codes in v0.1:

- `96127`
- `G8431`
- `G8510`
- `99484`

## Stage: Exclusion Validation

- `FR6_INVALID_BIPOLAR_HISTORY_FLAG`: `bipolar_history` must be boolean-like.
- `FR6_INVALID_PRIOR_YEAR_DEPRESSION_FLAG`: `prior_year_depression_dx` must be boolean-like.
- `FR6_MEMBER_EXCLUDED_BIPOLAR_HISTORY`: member is excluded due to bipolar history. Severity `WARN`.
- `FR6_MEMBER_EXCLUDED_PRIOR_DEPRESSION`: member is excluded due to prior-year depression diagnosis. Severity `WARN`.

## Determinism Notes

- Same input yields the same findings order because records are processed in file order and rules execute in a fixed stage order.
- Findings are machine-readable via `findings.json` and human-readable via `summary.md`.
