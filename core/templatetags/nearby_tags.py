"""Переносы стандартных карточек по макету; авторский текст CMS сохраняется."""
from django import template
from django.utils.html import strip_tags

register = template.Library()


@register.filter
def mobile_text(value):
    """Убирает настольные переносы, сохраняя пробелы между словами."""
    return ' '.join(str(value).split())


@register.filter
def mobile_hero(value):
    reference = ('Мы создаём место, где можно замедлиться,\n'
                 'восстановиться и прожить простые\n'
                 'моменты радости в окружении природы,\n'
                 'тепла и настоящей жизни.')
    return reference if mobile_text(value) == mobile_text(reference) else value


@register.filter
def mobile_intro(value):
    return mobile_text(strip_tags(str(value).replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ').replace('</p>', ' ')))


@register.filter
def mobile_quote(value):
    return mobile_text(value).replace('Так появился “Лучший сезон”', 'Так появился “Best Season”')


@register.filter
def mobile_gallery(value):
    return mobile_text(value).replace('вечернего разговора за чашкой чая', 'разговора за чашкой чая')


@register.filter
def brand_title(value):
    return "Лучший сезон" if value == "Лучший Сезон" else value

TITLES = {
    'Усадьба "Поленово"': 'Усадьба\n”Поленово”',
    'деревня Ф. Конюхова': 'деревня\nФ. Конюхова',
    'деревня "Бёхово"': 'деревня\n”Бёхово”',
}
DESCRIPTIONS = [
    'В 3 км от нас невероятной красоты\nусадьба русского художника Василия\nПоленова, которая по праву стала\nдостоянием Тульского края.',
    'В 6 км от нас Арт-проект всемирно\nизвестного путешественника\nФедора Конюхова - необычное\nпространство для вдохновения.',
    'В 5 км от нас находится старинная и\nживописная деревня Бёхово, которая\nв 2021 г. вошла в топ лучших\nдеревень мира по версии ООН.',
]


@register.filter
def nearby_title(value):
    return TITLES.get(value, value)


@register.filter
def nearby_description(value):
    def normalized(text):
        return ' '.join(text.replace('ё', 'е').replace('—', '-').split())
    for text in DESCRIPTIONS:
        if normalized(value) == normalized(text):
            return text
    return value


@register.filter
def gallery_lines(value):
    text = (
        'Копилку ваших самых счастливых дней может пополнить тот,\n'
        'который состоит из простых вещей: наблюдения за птицами,\n'
        'неторопливой прогулкой, знакомства с местными жителями\n'
        'нашей фермы, вечернего разговора за чашкой чая.'
    )
    return text if ' '.join(value.split()) == ' '.join(text.split()) else value
