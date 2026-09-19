"""Output contract shared by topic-analysis requests and validation."""
import json


TOPIC_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "primary_labels_selected": {"type": "array", "items": {"type": "string"}},
        "resolution_primary_labels": {"type": "array", "items": {"type": "string"}},
        "urgency": {"type": "string", "enum": ["none", "low", "medium", "high"]},
        "reflection_summary": {"type": "string"},
        "instructor_suggestions": {"type": "string"},
    },
    "required": ["primary_labels_selected", "resolution_primary_labels", "urgency",
                 "reflection_summary", "instructor_suggestions"],
    "additionalProperties": False,
}


def validate_topic_output(raw):
    try:
        result = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError as exc:
        raise ValueError("Response must be a valid JSON object.") from exc
    if not isinstance(result, dict):
        raise ValueError("Response must be a single top-level JSON object.")
    for field in TOPIC_OUTPUT_SCHEMA['required']:
        if field not in result:
            raise ValueError(f"Missing top-level field: {field}.")
    for field in ('primary_labels_selected', 'resolution_primary_labels'):
        labels = result[field]
        if not isinstance(labels, list) or not labels or not all(
            isinstance(label, str) and label.strip() for label in labels
        ):
            raise ValueError(f"{field} must be a nonempty array of label strings.")
    if len(result['primary_labels_selected']) != len(result['resolution_primary_labels']):
        raise ValueError("Each primary label must have one corresponding resolution label.")
    if result['urgency'] not in ('none', 'low', 'medium', 'high'):
        raise ValueError("urgency must be none, low, medium, or high.")
    for field in ('reflection_summary', 'instructor_suggestions'):
        if not isinstance(result[field], str):
            raise ValueError(f"{field} must be a string.")
    return result
