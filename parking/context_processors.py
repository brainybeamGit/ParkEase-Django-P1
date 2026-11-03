from django.conf import settings

def google_maps(request):
    """
    Exposes Google Maps Platform API keys to all Django templates.
    """
    maps_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    places_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', '')
    routes_key = getattr(settings, 'GOOGLE_ROUTES_API_KEY', '')

    return {
        'GOOGLE_MAPS_API_KEY': maps_key,
        'GOOGLE_PLACES_API_KEY': places_key,
        'GOOGLE_ROUTES_API_KEY': routes_key,
        'google_maps_api_key': maps_key,
    }
