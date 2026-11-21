"""Original legal PDFs supplied for the site, keyed by legal page slug."""

import re

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


LEGAL_TITLE_PREFIXES = {
    "soglasie-na-rassylku": "Согласие на рассылку электронных сообщений",
    "oferta": "Оферта на оказание услуг",
    "politika-konfidencialnosti": "Политика конфиденциальности «BEST SEASON»",
    "soglasie-na-obrabotku": "Согласие на обработку персональных данных",
}


@register.simple_tag
def legal_document_layout(slug, body):
    blocks = list(body)
    prefix = LEGAL_TITLE_PREFIXES.get(slug)
    layout = {"blocks": blocks}
    if not prefix or len(blocks) < 2:
        return layout

    title, revision = blocks[:2]
    if (
        title.block_type in {"paragraph", "heading"}
        and str(title.value).strip().casefold().startswith(prefix.casefold())
        and revision.block_type == "paragraph"
        and re.match(r"\s*(?:в редакции|редакция) от\s+\S", str(revision.value), re.I)
    ):
        layout.update(title=title.value, revision=revision.value, blocks=blocks[2:])
    return layout


@register.filter
def legal_paragraph_parts(value, slug):
    text = complete_legal_domain(value, slug)
    if slug == "soglasie-na-rassylku" and text.startswith("Я подтверждаю, что владею информацией"):
        return re.split(
            r"(?<=\.)\s+(?=Срок обработки персональных данных|Я подтверждаю, что действую)",
            text,
        )
    if slug == "oferta" and text.startswith("ИСПОЛНИТЕЛЬ:"):
        return re.split(r"\s+(?=ИП\s|ИНН:|ОГРНИП:|e-mail:)", text)
    if (
        slug == "politika-konfidencialnosti"
        and text.startswith("ИП ")
        and re.fullmatch(r"ИП [^:]+ ИНН:\s*\d+\s+ОГРНИП:\s*\d+\s*", text)
    ):
        return re.split(r"\s+(?=ИНН:|ОГРНИП:)", text)
    return [text]
