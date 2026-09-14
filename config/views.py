from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@never_cache
@require_GET
def health_check(request):
    """Process-level health probe; intentionally does not mutate or expose data."""
    return JsonResponse({"status": "ok"})
