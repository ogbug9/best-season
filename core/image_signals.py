"""Prepare editor uploads, including chooser/multiple-upload paths."""
import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from wagtail.images import get_image_model


@receiver(post_save, sender=get_image_model(), dispatch_uid='bs_prepare_editor_image')
def prepare_editor_image(sender, instance, raw=False, **kwargs):
    if raw or not instance.file:
        return
    image_id = instance.pk

    def prepare_committed():
        from core.management.commands.prepare_site_images import prepare
        from core.templatetags.media_tags import PRESETS, mobile_specs
        widths = {width for _, sizes, _ in PRESETS.values() for width in sizes}
        plan = {(image_id, f'width-{width}|format-{ext}') for width in widths for ext in ('webp', 'jpeg')}
        for preset in ('hero_mobile', 'promo_mobile'):
            plan.update((image_id, spec) for _, _, spec in mobile_specs(preset))
        failures = prepare(plan)
        if failures:
            logging.getLogger(__name__).warning('Image %s: %s variants unavailable; original retained.', image_id, failures)

    transaction.on_commit(prepare_committed)
