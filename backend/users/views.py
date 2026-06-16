from __future__ import annotations

import json

from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import User, BlockedUser


def _parse_json(request):
	try:
		return json.loads(request.body.decode('utf-8'))
	except json.JSONDecodeError:
		return None


def _user_payload(user: User) -> dict:
	return {
		'id': user.id,
		'name': user.username,
		'email': user.email,
	}


def _preferences_payload(user: User) -> dict:
	return {
		'greenery': user.preference_greenery,
		'noise': user.preference_noise,
		'airQuality': user.preference_air_quality,
	}


def _send_verification_email(user: User) -> None:
	uid = urlsafe_base64_encode(force_bytes(user.pk))
	token = default_token_generator.make_token(user)
	link = f'{settings.BACKEND_URL}/api/auth/verify-email?uid={uid}&token={token}'
	send_mail(
		'Confirm your email',
		f'Click the link to activate your account: {link}',
		settings.DEFAULT_FROM_EMAIL,
		[user.email],
	)


@ensure_csrf_cookie
@require_GET
def csrf_view(request):
	return JsonResponse({'detail': 'CSRF cookie set.'})


@require_POST
def signup_view(request):
	payload = _parse_json(request)
	if payload is None:
		return JsonResponse({'error': 'INVALID_JSON', 'message': 'Request body must be valid JSON.'}, status=400)

	username = (payload.get('username') or '').strip()
	email = (payload.get('email') or '').strip().lower()
	password = payload.get('password') or ''

	if not username or not email or not password:
		return JsonResponse({'error': 'INVALID_PAYLOAD', 'message': 'Username, email, and password are required.'}, status=400)

	try:
		validate_password(password)
		user = User.objects.create_user(email=email, username=username, password=password, is_active=False)
	except ValidationError as error:
		return JsonResponse({'error': 'INVALID_PASSWORD', 'message': ' '.join(error.messages)}, status=400)
	except Exception as error:
		return JsonResponse({'error': 'SIGNUP_FAILED', 'message': str(error)}, status=400)

	_send_verification_email(user)
	return JsonResponse({'detail': 'Account created. Check your email to confirm your address.'}, status=201)


@require_GET
def verify_email_view(request):
	try:
		user = User.objects.get(pk=urlsafe_base64_decode(request.GET.get('uid', '')).decode())
	except (ValueError, User.DoesNotExist):
		return JsonResponse({'error': 'INVALID_LINK', 'message': 'Invalid verification link.'}, status=400)

	if not default_token_generator.check_token(user, request.GET.get('token', '')):
		return JsonResponse({'error': 'INVALID_TOKEN', 'message': 'This verification link is invalid or has expired.'}, status=400)

	user.is_active = True
	user.save(update_fields=['is_active'])
	return JsonResponse({'detail': 'Email confirmed. You can now log in.'}, status=200)


@require_POST
def login_view(request):
	payload = _parse_json(request)
	if payload is None:
		return JsonResponse({'error': 'INVALID_JSON', 'message': 'Request body must be valid JSON.'}, status=400)

	email = (payload.get('email') or '').strip().lower()
	password = payload.get('password') or ''

	if not email or not password:
		return JsonResponse({'error': 'INVALID_PAYLOAD', 'message': 'Email and password are required.'}, status=400)

	user = authenticate(request, email=email, password=password)
	if user is None:
		return JsonResponse({'error': 'INVALID_CREDENTIALS', 'message': 'Invalid email or password.'}, status=400)

	auth_login(request, user)
	return JsonResponse({'user': _user_payload(user)}, status=200)


@require_POST
def logout_view(request):
	auth_logout(request)
	return JsonResponse({'detail': 'Logged out.'}, status=200)


@require_GET
def me_view(request):
	if not request.user.is_authenticated:
		return JsonResponse({'error': 'UNAUTHORIZED', 'message': 'Authentication required.'}, status=401)

	return JsonResponse({'user': _user_payload(request.user)}, status=200)


@require_http_methods(['GET', 'PUT'])
def preferences_view(request):
	if not request.user.is_authenticated:
		return JsonResponse({'error': 'UNAUTHORIZED', 'message': 'Authentication required.'}, status=401)

	if request.method == 'GET':
		return JsonResponse({'preferences': _preferences_payload(request.user)}, status=200)

	payload = _parse_json(request)
	if payload is None:
		return JsonResponse({'error': 'INVALID_JSON', 'message': 'Request body must be valid JSON.'}, status=400)

	def parse_value(key, fallback):
		if key not in payload:
			return fallback
		try:
			value = int(payload[key])
		except (TypeError, ValueError):
			raise ValueError(f'{key} must be an integer.')
		if value < 0 or value > 100:
			raise ValueError(f'{key} must be between 0 and 100.')
		return value

	try:
		request.user.preference_greenery = parse_value('greenery', request.user.preference_greenery)
		request.user.preference_noise = parse_value('noise', request.user.preference_noise)
		request.user.preference_air_quality = parse_value('airQuality', request.user.preference_air_quality)
	except ValueError as error:
		return JsonResponse({'error': 'INVALID_PAYLOAD', 'message': str(error)}, status=400)

	request.user.save(update_fields=['preference_greenery', 'preference_noise', 'preference_air_quality'])
	return JsonResponse({'preferences': _preferences_payload(request.user)}, status=200)

@require_POST
def block_user_view(request):
	if not request.user.is_authenticated:
		return JsonResponse({'error': 'UNAUTHORIZED', 'message': 'Authentication required.'}, status=401)

	payload = _parse_json(request)
	if payload is None:
		return JsonResponse({'error': 'INVALID_JSON', 'message': 'Request body must be valid JSON.'}, status=400)

	user_id = payload.get('userId')
	if user_id is None:
		return JsonResponse({'error': 'INVALID_PAYLOAD', 'message': 'User ID is required.'}, status=400)

	if request.user.id == user_id:
		return JsonResponse({'error': 'INVALID_PAYLOAD', 'message': 'You cannot block yourself.'}, status=400)

	try:
		user_to_block = User.objects.get(pk=user_id)
	except User.DoesNotExist:
		return JsonResponse({'error': 'NOT_FOUND', 'message': 'User not found.'}, status=404)

	BlockedUser.objects.get_or_create(blocker=request.user, blocked=user_to_block)
	return JsonResponse({'detail': 'User blocked successfully.'}, status=200)
