from common.exceptions import InvalidOperationError

def registered_operations_handler(registry, event, context):
    """Handle requests using an operations registry

    Sample payload:
    {
        'action': 'operation_name',
        'payload': {
            ...
        }
    }
    """
    if 'action' not in event:
        raise InvalidOperationError(f"No action found in the request")

    action = event['action']
    if action not in registry:
        raise InvalidOperationError(f"Invalid action: '{action}'")

    return registry[action](event.get('payload', {}), context)
