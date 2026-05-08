"""
CBC Platform — Custom Exception Handler
Returns consistent error envelopes across all API endpoints.

Shape:
  {
    "status": "error",
    "code": 400,
    "message": "A human-readable summary",
    "errors": { "field": ["detail"] }   ← only on validation errors
  }
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "status": "error",
            "code": response.status_code,
            "message": _extract_message(response.data),
        }
        # Attach field-level errors for validation failures (HTTP 400)
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_payload["errors"] = response.data
        response.data = error_payload

    return response


def _extract_message(data):
    """Pull a top-level human-readable message from DRF error data."""
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        # Grab first field error
        for key, val in data.items():
            if isinstance(val, list) and val:
                return f"{key}: {val[0]}"
        return "Validation failed. Check the errors field for details."
    if isinstance(data, list) and data:
        return str(data[0])
    return "An unexpected error occurred."
