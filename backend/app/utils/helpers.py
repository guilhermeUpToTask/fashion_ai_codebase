from logging import Logger
import logging
from typing import Type, TypeVar

from pydantic import BaseModel, TypeAdapter, ValidationError
import requests

T = TypeVar("T") 
def parse_json_response(response: requests.Response, expected_type: Type[T]) -> T:
    """
    Parse JSON from a requests.Response and validate it as expected_type.

    Args:
        response: requests.Response with JSON payload
        expected_type: a Python type or Pydantic model type

    Returns:
        Parsed and validated object of type T
    """
    payload = response.json()
    adapter = TypeAdapter(expected_type)
    return adapter.validate_python(payload)

T = TypeVar("T", bound=BaseModel)

def safe_post_and_parse(url: str, payload: dict, model: Type[T], logger:Logger) -> T:
    """
    Send a POST request and parse JSON into a Pydantic model.
    Always logs structured errors and raises to allow retrying.
    """
    response = requests.post(url, json=payload)
    status_code = response.status_code

    try:
        data = response.json()
    except ValueError as e:
        # Couldn't parse JSON at all
        logger.error(
            "Failed to parse JSON from service response",
            extra={
                "url": url,
                "status_code": status_code,
                "raw_response": response.text[:500],
                "exception": str(e),
            },
            exc_info=True
        )
        raise

    try:
        return model.model_validate(data)
    except ValidationError as e:
        # JSON structure is wrong (validation failed)
        logger.error(
            "Response validation failed against model",
            extra={
                "url": url,
                "status_code": status_code,
                "parsed_response": data,
                "exception": str(e),
            },
            exc_info=True
        )
        raise


logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

def safe_request_and_parse(
    *,
    method: str = "GET",
    url: str,
    payload: dict | None = None,
    headers: dict | None = None,
    params: dict | None = None,
    model: Type[T],
    timeout: int = 30,
) -> T:
    """
    Send an HTTP request and parse JSON response into a Pydantic model.
    Logs detailed errors and raises exceptions to allow retry handling.

    Args:
        method: HTTP method ("GET", "POST", "PUT", etc.)
        url: Request URL
        payload: JSON payload for POST/PUT/PATCH requests
        headers: Optional HTTP headers
        params: Optional query parameters for GET requests
        model: Pydantic model class to validate response JSON against
        timeout: Request timeout in seconds

    Returns:
        Instance of `model` validated from JSON response

    Raises:
        requests.HTTPError, requests.RequestException on network issues
        ValueError on JSON decoding errors
        pydantic.ValidationError on schema validation errors
    """
    try:
        response = requests.request(
            method=method,
            url=url,
            json=payload,
            headers=headers,
            params=params,
            timeout=timeout,
        )
    except requests.RequestException as e:
        logger.error(
            f"Request error during {method} {url}",
            exc_info=True,
            extra={"method": method, "url": url},
        )
        raise

    # No raise_for_status(), to allow error body inspection/logging

    status_code = response.status_code

    try:
        data = response.json()
    except ValueError as e:
        logger.error(
            "Failed to parse JSON from response",
            extra={
                "method": method,
                "url": url,
                "status_code": status_code,
                "raw_response": response.text[:500],
                "exception": str(e),
            },
            exc_info=True,
        )
        raise

    try:
        return model.model_validate(data)
    except ValidationError as e:
        logger.error(
            "Response validation failed",
            extra={
                "method": method,
                "url": url,
                "status_code": status_code,
                "parsed_response": data,
                "exception": str(e),
            },
            exc_info=True,
        )
        raise