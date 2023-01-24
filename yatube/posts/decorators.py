from functools import WRAPPER_ASSIGNMENTS, wraps

from django.views.decorators.cache import cache_page


def cache_on_auth(timeout):
    """
    Caches views up to two times: Once for authenticated users, and
    once for unauthenticated users.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=WRAPPER_ASSIGNMENTS)
        def _wrapped_view(request, *args, **kwargs):
            result = cache_page(
                timeout,
                key_prefix=(f"_auth_{request.user.is_authenticated}_"))
            return result(view_func)(request, *args, **kwargs)
        return _wrapped_view
    return decorator