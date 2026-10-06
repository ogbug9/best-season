from django.test import TestCase
from importlib import import_module
from unittest.mock import patch
from django.apps import apps
from django.core.cache import cache
from django.db import connection
from django.urls import reverse
from wagtail.models import Site
from forms.models import FormSubmission
from forms.notifications import _lines
from .models import Promotion, PromotionsPage


class PromotionRequestTests(TestCase):
    def setUp(self):
        cache.clear()
        root = Site.objects.get(is_default_site=True).root_page
        self.page = root.add_child(instance=PromotionsPage(title='Акции', slug='akcii'))
        self.page.save_revision().publish()

    def test_hidden_card_not_rendered_and_request_has_topic_and_form(self):
        Promotion.objects.create(title='Hidden card', slug='hidden', is_visible=False)
        Promotion.objects.create(title='Visible card', slug='visible', cta_type='request')
        response = self.client.get(self.page.url)
        self.assertNotContains(response, 'Hidden card')
        self.assertContains(response, 'data-promotion-request-open')
        self.assertContains(response, 'data-topic="Акция: Visible card"')
        self.assertContains(response, 'data-promotion-request-modal')
        self.assertContains(response, 'name="topic"')

    @patch('forms.views.notify')
    def test_topic_saved_only_after_valid_submission(self, notify):
        response = self.client.post(reverse('forms:submit', args=['feedback']), {
            'name':'Тест', 'phone':'+79990001122', 'consent_given':'on',
            'topic':'Акция: День рождения', 'source_url':self.page.url,
        })
        self.assertEqual(response.status_code,302)
        self.assertIn('form=ok',response.url)
        self.assertIn('ft=feedback',response.url)
        submission=FormSubmission.objects.get()
        self.assertEqual(submission.topic,'Акция: День рождения')
        self.assertIn('Тема: Акция: День рождения',_lines(submission))
        self.assertEqual(notify.call_count,1)

    def test_data_change_is_idempotent_and_preserves_editor_text(self):
        migration=import_module('promotions.migrations.0006_night_promotion_actions')
        for slug,title,text,order in migration.SEED:
            Promotion.objects.create(slug=slug,title=title,short_description=text,sort_order=order)
        editor=Promotion.objects.get(slug='gostepriimstvo')
        editor.short_description='Авторский текст';editor.save()
        schema=type('Schema',(),{'connection':connection})()
        migration.apply_actions(apps,schema);migration.apply_actions(apps,schema)
        self.assertEqual(Promotion.objects.get(slug='den-rozhdeniya').cta_type,'request')
        self.assertFalse(Promotion.objects.get(slug='may-sentyabr').is_visible)
        self.assertEqual(Promotion.objects.get(slug='oktyabr-aprel').sort_order,30)
        self.assertEqual(Promotion.objects.get(slug='gostepriimstvo').short_description,'Авторский текст')
        self.assertEqual(Promotion.objects.get(slug='gostepriimstvo').cta_type,'booking')
        self.assertEqual(Promotion.objects.filter(slug='podarochnyy-sertifikat').count(),1)


class SeasonalTariffTests(TestCase):
    def test_yearly_window_switches_on_30_april_and_30_september(self):
        from datetime import date
        from .models import in_season
        summer, winter = ('30.04', '29.09'), ('30.09', '29.04')
        for day, shown in [(date(2026, 10, 6), winter), (date(2027, 4, 29), winter), (date(2027, 4, 30), summer),
                           (date(2027, 9, 29), summer), (date(2027, 9, 30), winter), (date(2027, 1, 1), winter)]:
            self.assertTrue(in_season(day, *shown), day)
            other = summer if shown == winter else winter
            self.assertFalse(in_season(day, *other), day)

    def test_migration_sets_both_seasons_on_one_place_and_keeps_edited_cards(self):
        seed = import_module('promotions.migrations.0006_night_promotion_actions')
        for slug, title, text, order in seed.SEED:
            Promotion.objects.create(slug=slug, title=title, short_description=text, sort_order=order)
        schema = type('Schema', (), {'connection': connection})()
        seed.apply_actions(apps, schema)
        Promotion.objects.filter(slug='may-sentyabr').update(title='Свой заголовок')
        import_module('promotions.migrations.0008_seasonal_tariffs').apply_seasons(apps, schema)
        winter = Promotion.objects.get(slug='oktyabr-aprel')
        self.assertEqual((winter.season_start, winter.season_end, winter.sort_order), ('30.09', '29.04', 30))
        self.assertEqual(Promotion.objects.get(slug='may-sentyabr').season_start, '')

    def test_card_visibility_follows_today(self):
        from datetime import date
        Promotion.objects.create(slug='s', title='S', season_start='30.04', season_end='29.09')
        with patch('promotions.models.timezone.localdate', return_value=date(2026, 10, 6)):
            self.assertFalse(Promotion.objects.get(slug='s').is_active)
        with patch('promotions.models.timezone.localdate', return_value=date(2027, 5, 1)):
            self.assertTrue(Promotion.objects.get(slug='s').is_active)
