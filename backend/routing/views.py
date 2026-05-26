from __future__ import annotations

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import calculate_route
from .services.models import RoutingError


@csrf_exempt
@require_POST
def walking_route_view(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse(
            {
                'error': 'INVALID_JSON',
                'message': 'Request body must be valid JSON.',
            },
            status=400,
        )

    start = payload.get('start')
    end = payload.get('end')
    weights = payload.get('weights')

    if not isinstance(start, dict) or not isinstance(end, dict):
        return JsonResponse(
            {
                'error': 'INVALID_PAYLOAD',
                'message': 'Both start and end coordinates are required.',
            },
            status=400,
        )

    if weights is not None and not isinstance(weights, dict):
        return JsonResponse(
            {
                'error': 'INVALID_PAYLOAD',
                'message': 'Weights must be an object when provided.',
            },
            status=400,
        )

    try:
        response_payload = calculate_route(
            start_payload=start,
            end_payload=end,
            weights_payload=weights,
        )
        return JsonResponse(response_payload, status=200)
    except (KeyError, TypeError, ValueError):
        return JsonResponse(
            {
                'error': 'INVALID_PAYLOAD',
                'message': 'Route coordinates and weights must be numeric.',
            },
            status=400,
        )
    except RoutingError as error:
        return JsonResponse(
            {
                'error': error.code,
                'message': error.message,
            },
            status=error.status_code,
        )
    except FileNotFoundError as error:
        return JsonResponse(
            {
                'error': 'GRAPH_NOT_READY',
                'message': str(error),
            },
            status=503,
        )
    except Exception:
        return JsonResponse(
            {
                'error': 'ROUTING_FAILED',
                'message': 'The route could not be calculated.',
            },
            status=500,
        )
