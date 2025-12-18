from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

def group_required(*group_names):
    """
    Requires user to be in any of the specified groups.

    Special rules:
    - Users in the `Owner` group bypass group checks and may access any
      view decorated with `@group_required(...)`.
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            # Owner users may access everything protected by this decorator
            if user.groups.filter(name='Owner').exists():
                return view_func(request, *args, **kwargs)
            # Otherwise require membership in one of the allowed groups
            if user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You do not have permission to access this resource.")
        return _wrapped
    return decorator
