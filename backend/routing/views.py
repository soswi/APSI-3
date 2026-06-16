from __future__ import annotations

import json
from datetime import datetime

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .services import calculate_route
from .services.models import RoutingError
from .models import RouteRecord, RouteShare
from users.models import User, BlockedUser
from django.db.models import Q


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

def _serialize_share(share: RouteShare) -> dict:
    return {
        'id': share.id,
        'sender': {
            'id': share.sender.id,
            'name': share.sender.username,
            'email': share.sender.email,
        },
        'status': share.status,
        'createdAt': share.created_at.isoformat(),
        'route': _serialize_route(share.route),
    }

@require_POST
def share_route_view(request, route_id: int):
    auth_response = _require_auth(request)
    if auth_response is not None:
        return auth_response

    payload = _parse_json(request)
    if payload is None:
        return JsonResponse({'error': 'INVALID_JSON', 'message': 'Request body must be valid JSON.'}, status=400)

    recipient_identifier = (payload.get('recipient') or '').strip()
    if not recipient_identifier:
        return JsonResponse({'error': 'INVALID_PAYLOAD', 'message': 'Recipient must be provided.'}, status=400)

    try:
        route = RouteRecord.objects.get(id=route_id, user=request.user)
    except RouteRecord.DoesNotExist:
        return JsonResponse({'error': 'NOT_FOUND', 'message': 'Route not found.'}, status=404)

    # find user by email or username
    try:
        recipient = User.objects.get(Q(email=recipient_identifier) | Q(username=recipient_identifier))
    except User.DoesNotExist:
        return JsonResponse({'error': 'NOT_FOUND', 'message': 'User not found.'}, status=404)
    except User.MultipleObjectsReturned:
        recipient = User.objects.filter(Q(email=recipient_identifier) | Q(username=recipient_identifier)).first()

    if recipient.id == request.user.id:
        return JsonResponse({'error': 'INVALID_PAYLOAD', 'message': 'You cannot share a route with yourself.'}, status=400)

    # check block status
    if BlockedUser.objects.filter(blocker=recipient, blocked=request.user).exists():
        return JsonResponse({'error': 'BLOCKED', 'message': 'This user cannot receive shares from you.'}, status=403)

    share, created = RouteShare.objects.get_or_create(
        sender=request.user,
        recipient=recipient,
        route=route,
        status='PENDING'
    )
    return JsonResponse({'share': _serialize_share(share)}, status=201 if created else 200)

@require_GET
def pending_shares_view(request):
    auth_response = _require_auth(request)
    if auth_response is not None:
        return auth_response

    shares = RouteShare.objects.select_related('sender', 'route').filter(recipient=request.user, status='PENDING').order_by('-created_at')
    
    # filter out blocks
    blocked_ids = BlockedUser.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
    if blocked_ids:
        shares = shares.exclude(sender_id__in=blocked_ids)
        
    return JsonResponse({'shares': [_serialize_share(share) for share in shares]}, status=200)

@require_POST
def accept_share_view(request, share_id: int):
    auth_response = _require_auth(request)
    if auth_response is not None:
        return auth_response

    try:
        share = RouteShare.objects.get(id=share_id, recipient=request.user, status='PENDING')
    except RouteShare.DoesNotExist:
        return JsonResponse({'error': 'NOT_FOUND', 'message': 'Share not found or already processed.'}, status=404)

    # clone RouteRecord
    new_route = RouteRecord.objects.create(
        user=request.user,
        name=f"Shared: {share.route.name}",
        saved=True,
        start_point=share.route.start_point,
        end_point=share.route.end_point,
        start_label=share.route.start_label,
        end_label=share.route.end_label,
        preferences=share.route.preferences,
        route=share.route.route,
        distance_m=share.route.distance_m
    )
    
    share.status = 'ACCEPTED'
    share.save(update_fields=['status', 'updated_at'])

    return JsonResponse({'route': _serialize_route(new_route)}, status=200)

@require_POST
def reject_share_view(request, share_id: int):
    auth_response = _require_auth(request)
    if auth_response is not None:
        return auth_response

    try:
        share = RouteShare.objects.get(id=share_id, recipient=request.user, status='PENDING')
    except RouteShare.DoesNotExist:
        return JsonResponse({'error': 'NOT_FOUND', 'message': 'Share not found or already processed.'}, status=404)

    share.status = 'REJECTED'
    share.save(update_fields=['status', 'updated_at'])

    return JsonResponse({'detail': 'Share rejected.'}, status=200)
