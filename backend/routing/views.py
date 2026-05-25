from __future__ import annotations

import json
from datetime import datetime

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .services import calculate_route
from .services.models import RoutingError
from .models import RouteRecord


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

    try:
        response_payload = calculate_route(
            start_payload=start,
            end_payload=end,
            weights_payload=weights if isinstance(weights, dict) else None,
        )
        return JsonResponse(response_payload, status=200)
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


def _parse_json(request):
    try:
        return json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return None


def _require_auth(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'UNAUTHORIZED', 'message': 'Authentication required.'}, status=401)
    return None


def _default_route_name(created_at: datetime) -> str:
    return f"Route {timezone.localtime(created_at).strftime('%d %b %H:%M')}"


def _serialize_route(record: RouteRecord) -> dict:
    return {
        'id': record.id,
        'createdAt': record.created_at.isoformat(),
        'name': record.name or _default_route_name(record.created_at),
        'saved': record.saved,
        'startPoint': record.start_point,
        'endPoint': record.end_point,
        'startLabel': record.start_label,
        'endLabel': record.end_label,
        'preferences': record.preferences,
        'route': record.route,
        'distance': record.distance_m,
    }


@require_http_methods(['GET', 'POST'])
def recent_routes_view(request):
    auth_response = _require_auth(request)
    if auth_response is not None:
        return auth_response

    if request.method == 'GET':
        recent = RouteRecord.objects.filter(user=request.user).order_by('-created_at')
        return JsonResponse({'routes': [_serialize_route(route) for route in recent]}, status=200)

    payload = _parse_json(request)
    if payload is None:
        return JsonResponse({'error': 'INVALID_JSON', 'message': 'Request body must be valid JSON.'}, status=400)

    start_point = payload.get('startPoint')
    end_point = payload.get('endPoint')
    route = payload.get('route')

    if not isinstance(start_point, dict) or not isinstance(end_point, dict) or not isinstance(route, list):
        return JsonResponse({'error': 'INVALID_PAYLOAD', 'message': 'Route geometry and points are required.'}, status=400)

    created_at = payload.get('createdAt')
    created_dt = timezone.now()
    if isinstance(created_at, str):
        try:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except ValueError:
            created_dt = timezone.now()

    record = RouteRecord.objects.create(
        user=request.user,
        created_at=created_dt,
        name=(payload.get('name') or '').strip(),
        saved=bool(payload.get('saved', False)),
        start_point=start_point,
        end_point=end_point,
        start_label=(payload.get('startLabel') or '').strip(),
        end_label=(payload.get('endLabel') or '').strip(),
        preferences=payload.get('preferences') or {},
        route=route,
        distance_m=float(payload.get('distance') or 0.0),
    )

    if not record.name:
        record.name = _default_route_name(record.created_at)
        record.save(update_fields=['name'])

    return JsonResponse({'route': _serialize_route(record)}, status=201)


@require_GET
def saved_routes_view(request):
    auth_response = _require_auth(request)
    if auth_response is not None:
        return auth_response

    saved_routes = RouteRecord.objects.filter(user=request.user, saved=True).order_by('-created_at')
    return JsonResponse({'routes': [_serialize_route(route) for route in saved_routes]}, status=200)


@require_http_methods(['PUT', 'DELETE'])
def saved_route_detail_view(request, route_id: int):
    auth_response = _require_auth(request)
    if auth_response is not None:
        return auth_response

    try:
        record = RouteRecord.objects.get(id=route_id, user=request.user)
    except RouteRecord.DoesNotExist:
        return JsonResponse({'error': 'NOT_FOUND', 'message': 'Route not found.'}, status=404)

    if request.method == 'DELETE':
        record.delete()
        return JsonResponse({'detail': 'Route deleted.'}, status=200)

    payload = _parse_json(request)
    if payload is None:
        return JsonResponse({'error': 'INVALID_JSON', 'message': 'Request body must be valid JSON.'}, status=400)

    name = (payload.get('name') or '').strip()
    record.name = name or record.name
    record.saved = bool(payload.get('saved', True))
    record.save(update_fields=['name', 'saved', 'updated_at'])

    return JsonResponse({'route': _serialize_route(record)}, status=200)
