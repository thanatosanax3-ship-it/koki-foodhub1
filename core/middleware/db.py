from django.db import close_old_connections


class DBConnectionMiddleware:
    """Ensure DB connections are closed/rotated before each request.

    This protects against 'InterfaceError: connection already closed' when
    worker processes hold stale DB connections (common on long-running WSGI
    workers or when the DB server closes idle connections).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Close old/stale connections before handling the request
        try:
            close_old_connections()
        except Exception:
            # If something goes wrong, don't block request processing; let
            # the view fail and surface a clearer error in logs.
            pass

        response = self.get_response(request)

        # Close old connections after the response as well to be safe
        try:
            close_old_connections()
        except Exception:
            pass

        return response
