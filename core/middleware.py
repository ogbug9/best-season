from django.conf import settings
from django.http import HttpResponsePermanentRedirect

UTM_FIELDS = ('utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term')


class CanonicalHostMiddleware:
    """301 с www и демо-домена на боевой одним прыжком, сразу на https."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        canonical = settings.CANONICAL_HOST
        if canonical and request.get_host().split(':')[0].lower() != canonical:
            return HttpResponsePermanentRedirect(f'https://{canonical}{request.get_full_path()}')
        return self.get_response(request)


class CampaignMiddleware:
    """Keep the latest campaign while visitors navigate to a form."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'GET' and any(key in request.GET for key in UTM_FIELDS):
            request.session['bs_utm'] = {key: request.GET.get(key, '')[:120] for key in UTM_FIELDS}
        request.bs_utm = request.session.get('bs_utm', {})
        return self.get_response(request)
