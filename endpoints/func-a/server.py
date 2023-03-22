from typing import TYPE_CHECKING

from scaleway_functions_python import local

if TYPE_CHECKING:
    from scaleway_functions_python.framework.v1.hints import Context, Event, Response


def handler(event: "Event", context: "Context") -> "Response":
    match event["path"]:
        case "/hello":
            return "Hello from function A"
        case "/goodbye":
            return "Goodbye from function A"
        case path:
            return {
                "statusCode": 404,
                "body": f"Path {path} not found for function A",
            }


if __name__ == "__main__":
    local.serve_handler(handler, host="0.0.0.0", port=80, debug=False)
