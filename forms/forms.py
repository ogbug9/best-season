"""Формы сайта — раздел 7 ТЗ.

Все четыре формы первой очереди плюс резервный сценарий п. 5.6 построены
на одном базовом классе: состав полей минимальный по разделу 11 ТЗ
(имя, телефон, email, даты, текст), защита от ботов одинаковая.

Капчи нет намеренно — п. 7 ТЗ предписывает honeypot и ограничение частоты
вместо неё. Капча отпугивает живых гостей и режет конверсию, а бороться
здесь нужно с примитивными ботами, которые заполняют все поля подряд.
"""

from django import forms
from django.utils import timezone

from .models import FormSubmission, FormType


class BaseRequestForm(forms.ModelForm):
    """Общая часть всех форм: контакты, согласие и ловушка для ботов."""

    # Ловушка. Поле спрятано от человека стилями и меткой aria-hidden,
    # но бот, заполняющий всё подряд, его заполнит — такую заявку отвергаем.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form__trap",
                "tabindex": "-1",
                "autocomplete": "off",
                "aria-hidden": "true",
            }
        ),
        label="Не заполняйте это поле",
    )

    consent_given = forms.BooleanField(
        required=True,
        # Без предзаполнения — прямое требование раздела 11 ТЗ:
        # согласие должно быть активным действием гостя.
        initial=False,
        label="Согласен на обработку персональных данных",
        error_messages={"required": "Без согласия мы не можем принять заявку."},
    )

    class Meta:
        model = FormSubmission
        fields = ["name", "phone", "email", "message", "consent_given"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "required": True}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "message": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "name": "Как вас зовут",
            "phone": "Телефон",
            "email": "Электронная почта",
            "message": "Сообщение",
        }

    form_type = FormType.FEEDBACK

    def clean_website(self):
        """Ловушка сработала — значит перед нами бот."""
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Заявка не принята.")
        return ""

    def clean(self):
        cleaned = super().clean()
        # Хотя бы один способ связи обязателен, иначе заявку не обработать
        if not cleaned.get("phone") and not cleaned.get("email"):
            raise forms.ValidationError(
                "Оставьте телефон или почту — иначе мы не сможем ответить."
            )
        return cleaned

    def save(self, commit=True, request=None, consent_version=""):
        submission = super().save(commit=False)
        submission.form_type = self.form_type
        submission.consent_at = timezone.now()
        submission.consent_version = consent_version

        if request is not None:
            submission.source_url = request.POST.get("source_url", "")[:500]
            for key in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"):
                setattr(submission, key, request.POST.get(key, "")[:120])

        if commit:
            submission.save()
        return submission


class FeedbackForm(BaseRequestForm):
    """Обратная связь — общая форма."""

    form_type = FormType.FEEDBACK


class TransferForm(BaseRequestForm):
    """Заявка на трансфер — п. 4.2.4 ТЗ, живёт на «Как добраться»."""

    form_type = FormType.TRANSFER

    class Meta(BaseRequestForm.Meta):
        fields = ["name", "phone", "email", "date_from", "guests", "message", "consent_given"]
        widgets = {
            **BaseRequestForm.Meta.widgets,
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "guests": forms.NumberInput(attrs={"min": 1, "max": 20}),
        }
        labels = {
            **BaseRequestForm.Meta.labels,
            "date_from": "Дата приезда",
            "guests": "Сколько гостей",
            "message": "Откуда забрать и другие детали",
        }


class CertificateForm(BaseRequestForm):
    """Подарочный сертификат."""

    form_type = FormType.CERTIFICATE

    class Meta(BaseRequestForm.Meta):
        labels = {
            **BaseRequestForm.Meta.labels,
            "message": "Пожелания к сертификату",
        }


class HouseQuestionForm(BaseRequestForm):
    """Вопрос со страницы дома. Дом подставляется скрытым полем,
    чтобы владелец сразу видел, о каком доме речь."""

    form_type = FormType.HOUSE_QUESTION

    class Meta(BaseRequestForm.Meta):
        fields = ["name", "phone", "email", "house", "message", "consent_given"]
        widgets = {**BaseRequestForm.Meta.widgets, "house": forms.HiddenInput()}
        labels = {**BaseRequestForm.Meta.labels, "message": "Ваш вопрос"}


class FallbackBookingForm(BaseRequestForm):
    """Резервный сценарий бронирования — п. 5.6 ТЗ.

    Показывается, если виджет Контура не загрузился за 5 секунд или вернул
    ошибку. Обязателен в первой очереди и проверяется на приёмке блокировкой
    домена виджета, поэтому форма должна работать полностью автономно.
    """

    form_type = FormType.FALLBACK

    class Meta(BaseRequestForm.Meta):
        fields = [
            "name", "phone", "email", "house",
            "date_from", "date_to", "guests", "message", "consent_given",
        ]
        widgets = {
            **BaseRequestForm.Meta.widgets,
            "house": forms.HiddenInput(),
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_to": forms.DateInput(attrs={"type": "date"}),
            "guests": forms.NumberInput(attrs={"min": 1, "max": 20}),
        }
        labels = {
            **BaseRequestForm.Meta.labels,
            "date_from": "Заезд",
            "date_to": "Выезд",
            "guests": "Гостей",
            "message": "Пожелания",
        }

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("date_from"), cleaned.get("date_to")
        if start and end and end <= start:
            self.add_error("date_to", "Дата выезда должна быть позже заезда.")
        return cleaned


FORM_CLASSES = {
    FormType.FEEDBACK: FeedbackForm,
    FormType.TRANSFER: TransferForm,
    FormType.CERTIFICATE: CertificateForm,
    FormType.HOUSE_QUESTION: HouseQuestionForm,
    FormType.FALLBACK: FallbackBookingForm,
}
