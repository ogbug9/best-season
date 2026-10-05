from django.test import SimpleTestCase

from core.faq_layout import AnswerParser, format_answer
from core.templatetags.layout_tags import about_mobile_paragraphs


class FaqLayoutTests(SimpleTestCase):
    def test_inline_link_and_entities_survive_reference_break(self):
        source = ('<p>Все скидки действуют при бронировании напрямую — на сайте или '
                  'через <a href="/route/?x=1&amp;y=2">нас.</a> '
                  '<em>У сторонних площадок свои цены и свои условия.</em></p>')
        output = format_answer(source, 'Действуют ли акции при бронировании через другие сайты?')
        self.assertIn('href="/route/?x=1&amp;y=2"', output)
        self.assertIn('<em><br class="faq__reference-break">', output)
        parsed = AnswerParser(); parsed.feed(output)
        original = AnswerParser(); original.feed(source)
        self.assertEqual(parsed.text.split(), original.text.split())

    def test_changed_editor_answer_is_not_reformatted(self):
        source = '<p>Условия редактора: <a href="/custom/">другая ссылка</a>.</p>'
        self.assertEqual(format_answer(source, 'Есть ли подарочные сертификаты?'), source)
        self.assertEqual(format_answer(source, 'Новый вопрос'), source)

    def test_mobile_copy_is_guarded_and_has_reference_line_endings(self):
        source = 'Что у нас происходит: новые постройки, сезонные акции, наши рубрики и места по соседству, куда стоит съездить.'
        rendered = str(about_mobile_paragraphs(source, 'diary'))
        self.assertIn('сезонные<br class="br-mob">затеи,', rendered)
        self.assertEqual(rendered.count('br-mob'), 2)
        self.assertIn('Описание редактора', str(about_mobile_paragraphs('Описание редактора', 'diary')))
