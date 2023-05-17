import scaleway.function.v1beta1 as sdk


def get_function_endpoint_by_name(
    api: sdk.FunctionV1Beta1API, namespace_name: str, function_name: str
) -> str | None:
    """Get the endpoint of a function by its name."""

    namespaces = api.list_namespaces_all(
        name=namespace_name,
    )
    if not namespaces:
        return None

    namespace = namespaces[0]
    functions = api.list_functions_all(namespace_id=namespace.id, name=function_name)

    return functions[0].domain_name if functions else None
