def confirmed_success(request):
    """Consume proof issued after saving; query parameters alone are insufficient."""
    if not hasattr(request, '_bs_confirmed_success'):
        value = ''
        if request.GET.get('form') == 'ok':
            proof = request.session.get('bs_form_success', {})
            if proof.get('type') == request.GET.get('ft') and proof.get('path') == request.path:
                value = proof['type']
                request.session.pop('bs_form_success', None)
        request._bs_confirmed_success = value
    return request._bs_confirmed_success
