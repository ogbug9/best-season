"""Original legal PDFs supplied for the site, keyed by legal page slug."""

from django import template
from django.templatetags.static import static

register = template.Library()

LEGAL_PDFS = {
    "oferta": "legal/booking-offer.pdf",
    "politika-konfidencialnosti": "legal/privacy-policy.pdf",
    "soglasie-na-obrabotku": "legal/personal-data-consent.pdf",
    "politika-cookies": "legal/cookies-policy.pdf",
    "soglasie-na-rassylku": "legal/marketing-consent.pdf",
}


@register.simple_tag
def legal_pdf_url(slug):
    path = LEGAL_PDFS.get(slug)
    return static(path) if path else ""
