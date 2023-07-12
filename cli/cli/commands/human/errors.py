import requests
from rich.style import Style
from scaleway import ScalewayException

from cli.console import console
from cli.gateway import KongAPIException

EXCEPTION_ERROR_STYLE = Style(color="red", bold=True)


def display_exception(exception: BaseException) -> None:
    """Display an exception, with a human-readable message."""
    message = f"{exception.__class__.__name__}: "
    if isinstance(exception, ScalewayException):
        message += parse_scaleway_exception_message(exception)
    elif isinstance(exception, KongAPIException):
        message += parse_kongapi_exception_message(exception)
    else:
        message += str(exception)
    console.print(message, style=EXCEPTION_ERROR_STYLE)


def parse_scaleway_exception_message(exception: ScalewayException) -> str:
    """Display a ScalewayException, with a human-readable message."""
    to_display = exception.response.text
    data = exception.response.json()

    to_display = data.get("message", to_display)

    if "type" in data:
        # Get the Scaleway standard error type
        # Not mapped in the Python SDK, but similar to the Golang SDK
        error_type = data["type"]
        # Replace the underscore with a space, and capitalize the first letter
        error_type = error_type.replace("_", " ").capitalize()
        to_display = f"{error_type}: {to_display}"

    if "help_message" in data:
        to_display += f"\nHelp message:\n{data['help_message']}"

    return to_display


def parse_kongapi_exception_message(exception: KongAPIException) -> str:
    """Display a KongAPIException, with a human-readable message."""
    # Try to parse as JSON
    try:
        data = exception.response.json()
        # If we can parse it, display the message
        return data["message"]
    except requests.exceptions.JSONDecodeError:
        # Might happen when the exception happens at the ingress level
        # and the response is not JSON
        return exception.response.text
