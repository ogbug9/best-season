from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import FormSubmission


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

    list_display = ["created_at", "form_type", "name", "phone", "status"]
    list_filter = ["form_type", "status", "created_at"]
    search_fields = ["name", "phone", "email", "message"]
    ordering = ["-created_at"]

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
