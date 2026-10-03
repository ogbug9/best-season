"""Structured content: text and images only; no HTML, CSS or arbitrary embeds."""
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.contrib.table_block.blocks import TableBlock


class AboutPhotoBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=False, label='Фотография')
    alt = blocks.CharBlock(required=False, label='Описание фотографии')
    crop = blocks.ChoiceBlock(
        choices=[(key, key) for key in (
            'aerial', 'story-moss', 'story-terrace', 'story-season',
            'pillar-farm', 'pillar-slow', 'pillar-comfort',
            'value-journey', 'value-pleasure', 'value-trust', 'value-friendship', 'value-sharing', 'value-care',
            'pet-snezhka', 'pet-dymok', 'diary-holidays', 'diary-ayka', 'diary-car',
        )], required=False, label='Кадрирование исходного макета',
    )


class AboutCardBlock(AboutPhotoBlock):
    title = blocks.TextBlock(label='Заголовок (переносы строк сохраняются)')
    lead = blocks.TextBlock(required=False, label='Подводка')
    text = blocks.TextBlock(required=False, label='Текст')
    # Visual slots belong to the template, not to editable CSS/classes.


class AboutPetBlock(AboutPhotoBlock):
    name = blocks.CharBlock(label='Имя')
    copy = blocks.TextBlock(label='Подпись')
    details = blocks.TextBlock(label='Подробности')


class AboutDiaryBlock(AboutPhotoBlock):
    title = blocks.TextBlock(label='Заголовок')
    url = blocks.URLBlock(required=False, label='Ссылка на запись')


class AboutContentBlock(blocks.StructBlock):
    hero_title = blocks.CharBlock(label='Заголовок первого экрана')
    hero_text = blocks.TextBlock(label='Текст первого экрана')
    intro = blocks.ListBlock(blocks.TextBlock(), label='Вступление: абзацы')
    story_first = blocks.TextBlock(label='История: начало')
    story_name_lead = blocks.CharBlock(label='История: подводка к названию')
    story_name = blocks.CharBlock(label='История: название')
    story_name_text = blocks.TextBlock(label='История: продолжение')
    story_last = blocks.TextBlock(label='История: завершение')
    motto = blocks.TextBlock(label='Девиз')
    history_photos = blocks.ListBlock(AboutPhotoBlock(), min_num=4, max_num=4, label='Фото истории (4 позиции)')
    pillars_title = blocks.CharBlock(label='Заголовок столпов')
    pillars = blocks.ListBlock(AboutCardBlock(), min_num=3, max_num=3, label='Три столпа')
    values_title = blocks.CharBlock(label='Заголовок ценностей')
    values = blocks.ListBlock(AboutCardBlock(), min_num=1, label='Ценности')
    pets_title = blocks.CharBlock(label='Заголовок питомцев')
    pets_text = blocks.TextBlock(label='Текст о питомцах')
    pets = blocks.ListBlock(AboutPetBlock(), label='Питомцы')
    diary_title = blocks.CharBlock(label='Заголовок дневника')
    diary_text = blocks.TextBlock(label='Текст дневника')
    diary = blocks.ListBlock(AboutDiaryBlock(), label='Записи дневника')
    map_title = blocks.CharBlock(label='Заголовок карты')
    map_text = blocks.TextBlock(label='Текст карты')


LEGAL_BLOCKS = [
    ('heading', blocks.CharBlock(label='Заголовок раздела')),
    ('paragraph', blocks.TextBlock(label='Абзац (точный текст документа)')),
    ('list', blocks.ListBlock(blocks.TextBlock(), label='Список (исходная нумерация/маркеры)')),
    ('table', TableBlock(label='Таблица', table_options={'renderer': 'text'})),
]
