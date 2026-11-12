"""Original legal PDFs supplied for the site, keyed by legal page slug."""

from django import template
from django.templatetags.static import static

register = template.Library()


@register.filter
def complete_legal_domain(value, slug):
    """Complete known blank addresses without changing stored editorial copy."""
    from core.legal_domain import fill_legal_domain

    return fill_legal_domain(slug, [{"value": str(value)}])[0]["value"]

LEGAL_PDFS = {
    "oferta": "legal/booking-offer.pdf",
    "politika-konfidencialnosti": "legal/privacy-policy.pdf",
    "soglasie-na-obrabotku": "legal/personal-data-consent.pdf",
    "politika-cookies": "legal/cookies-policy.pdf",
    "soglasie-na-rassylku": "legal/marketing-consent.pdf",
}

# The supplied PDFs remain the original CMS backfill sources; these two
# typeset copies complete the blank site addresses for visitors to download.
LEGAL_DOWNLOAD_PDFS = {
    **LEGAL_PDFS,
    "oferta": "legal/booking-offer-site.pdf",
    "politika-konfidencialnosti": "legal/privacy-policy-site.pdf",
}


@register.simple_tag
def legal_pdf_url(slug):
    path = LEGAL_DOWNLOAD_PDFS.get(slug)
    return static(path) if path else ""
