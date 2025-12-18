import logging
import traceback
import uuid
from django.http import JsonResponse, HttpResponse

logger = logging.getLogger(__name__)

class ForecastExceptionMiddleware:
    """Catch uncaught exceptions for forecast endpoints and return a controlled
    response that includes an Error ID which can be correlated with logs.

    - For XHR/JSON requests (or /forecast/api/*) return JSON: {error, id}
    - For browser page requests return a short HTML message with the id
    - When an admin requests with ?debug=1 include the full traceback
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exc:
            tb = traceback.format_exc()
            error_id = uuid.uuid4().hex[:8]
            logger.exception('Unhandled exception for path %s (id=%s): %s\n%s', request.path, error_id, str(exc), tb)

            accept = (request.headers.get('accept') or '').lower()
            is_xhr = request.headers.get('x-requested-with') == 'XMLHttpRequest'
            wants_json = is_xhr or ('application/json' in accept) or request.path.startswith('/forecast/api/')

            try:
                is_admin = hasattr(request, 'user') and getattr(request.user, 'is_superuser', False)
            except Exception:
                is_admin = False

            # Admins can request debug traces
            if wants_json:
                if request.GET.get('debug') and is_admin:
                    return JsonResponse({'error': 'Internal Server Error', 'trace': tb, 'id': error_id}, status=500)
                return JsonResponse({'error': 'Internal Server Error', 'id': error_id}, status=500)

            # HTML response for normal browser requests
            if request.GET.get('debug') and is_admin:
                return HttpResponse('<pre style="white-space:pre-wrap;">Server Error (500) (id=' + error_id + ')\n\n' + tb + '</pre>', status=500)

            return HttpResponse(f'Server Error (500) - Forecasts temporarily unavailable. Error ID: {error_id}', status=500)
