from django.db.models import Prefetch
from django.urls import path, reverse
from django.utils.html import format_html_join
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.admin.ui.tables import Column
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .admin_views import download_attachment, export_csv

from .models import FormSubmission, PartnerAttachment


def attachment_links(submission):
    return format_html_join(
        ", ", '<a href="{}">{}</a>',
        ((reverse("forms_download_attachment", args=[attachment.pk]), attachment.name)
         for attachment in submission.attachments.all()),
    )


class FormSubmissionViewSet(SnippetViewSet):
    """Список заявок в админке — п. 7.5 ТЗ.

    Заявки приходят с сайта, поэтому создавать их руками не нужно:
    редактор только просматривает и меняет статус. Данные отправителя
    доступны на чтение, редактирование полей ПД не предполагается.
    """

    model = FormSubmission
    icon = "mail"
    menu_label = "Заявки"
    menu_order = 200
    add_to_admin_menu = True

    list_display = [
        "created_at", "form_type", "topic", "name", "phone", "status",
        Column("attachments", label="Файлы", accessor=attachment_links),
    ]
    list_filter = ["form_type", "status", "created_at"]
    search_fields = ["name", "phone", "email", "topic", "message"]
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return FormSubmission.objects.prefetch_related(
            Prefetch("attachments", queryset=PartnerAttachment.objects.only("submission_id", "name")),
        )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("status"),
                FieldPanel("form_type", read_only=True),
                FieldPanel("created_at", read_only=True),
                FieldPanel("notified_at", read_only=True),
            ],
            heading="Обработка",
        ),
        MultiFieldPanel(
            [
                FieldPanel("name", read_only=True),
                FieldPanel("phone", read_only=True),
                FieldPanel("email", read_only=True),
                FieldPanel("message", read_only=True),
                FieldPanel("topic", read_only=True),
            ],
            heading="Контакт",
        ),
        MultiFieldPanel(
            [
                FieldPanel("house", read_only=True),
                FieldPanel("date_from", read_only=True),
                FieldPanel("date_to", read_only=True),
                FieldPanel("guests", read_only=True),
            ],
            heading="Детали заявки",
        ),
        MultiFieldPanel(
            [
                FieldPanel("source_url", read_only=True),
                FieldPanel("utm_source", read_only=True),
                FieldPanel("utm_medium", read_only=True),
                FieldPanel("utm_campaign", read_only=True),
            ],
            heading="Источник",
        ),
        MultiFieldPanel(
            [
                FieldPanel("consent_given", read_only=True),
                FieldPanel("consent_version", read_only=True),
                FieldPanel("consent_at", read_only=True),
            ],
            heading="Согласие на обработку ПД",
        ),
    ]


register_snippet(FormSubmissionViewSet)


@hooks.register("register_admin_urls")
def forms_admin_urls():
    return [
        path("zayavki/export/", export_csv, name="forms_export_csv"),
        path("zayavki/attachment/<int:pk>/", download_attachment, name="forms_download_attachment"),
    ]


@hooks.register("register_admin_menu_item")
def forms_export_menu():
    """Отдельный пункт меню: выгрузка заявок в CSV — требование п. 7.5 ТЗ."""
    return MenuItem(
        "Выгрузить заявки",
        reverse("forms_export_csv"),
        icon_name="download",
        order=210,
    )
