"""Fill the explicitly blank site addresses in the supplied legal copy."""

REPLACEMENTS = {
    "oferta": (
        ("в области доменных имён https://.", "в области доменных имён https://best-season.online."),
        ("в области доменных имён https://,", "в области доменных имён https://best-season.online,"),
        ("через сайт https://,", "через сайт https://best-season.online,"),
        ("на сайте https:// с использованием", "на сайте https://best-season.online с использованием"),
        ("по адресу https://..", "по адресу https://best-season.online.."),
        ("на сайте https://.", "на сайте https://best-season.online."),
        ("на сайте https://", "на сайте https://best-season.online"),
    ),
    "politika-konfidencialnosti": (
        ("сайта Оператора адрес сайта (далее", "сайта Оператора https://best-season.online (далее"),
        ("по адресу: https:// Пользователь", "по адресу: https://best-season.online Пользователь"),
    ),
}


def fill_legal_domain(slug, blocks):
    for block in blocks or []:
        value = block.get("value") if isinstance(block, dict) else None
        if not isinstance(value, str):
            continue
        for old, new in REPLACEMENTS.get(slug, ()):
            # The final offer line ends at the placeholder; avoid matching an
            # already completed address or an editor's different URL.
            if old == "на сайте https://":
                if value.endswith(old):
                    value = value[:-len(old)] + new
            else:
                value = value.replace(old, new)
        block["value"] = value
    return blocks
