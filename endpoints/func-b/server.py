from typing import TYPE_CHECKING

from scaleway_functions_python import local

if TYPE_CHECKING:
    from scaleway_functions_python.framework.v1.hints import Context, Event, Response


def handler(event: "Event", context: "Context") -> "Response":
    match event["path"]:
        case "/hello":
            return "Hello from function B"
        case "/goodbye":
            return "Goodbye from function B"
        case path:
            return {
                "statusCode": 404,
                "body": f"Path {path} not found for function B",
            }


if __name__ == "__main__":
    local.serve_handler(handler, host="0.0.0.0", port=80, debug=False)
