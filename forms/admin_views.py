"""Выгрузка заявок в CSV — п. 7.5 ТЗ.

Отдельной вьюхой, а не готовым плагином: набор колонок должен точно
совпадать с тем, что мы храним, включая версию согласия и UTM. Файл
отдаётся с BOM, иначе Excel открывает кириллицу кракозябрами, а заказчик
будет смотреть заявки именно в нём.
"""

import csv

from django.http import HttpResponse
from django.utils import timezone

from .models import FormSubmission

COLUMNS = [
    ("created_at", "Получена"),
    ("form_type", "Тип формы"),
    ("status", "Статус"),
    ("name", "Имя"),
    ("phone", "Телефон"),
    ("email", "Почта"),
    ("house", "Дом"),
    ("date_from", "Заезд"),
    ("date_to", "Выезд"),
    ("guests", "Гостей"),
    ("message", "Сообщение"),
    ("source_url", "Страница"),
    ("utm_source", "utm_source"),
    ("utm_medium", "utm_medium"),
    ("utm_campaign", "utm_campaign"),
    ("consent_given", "Согласие"),
    ("consent_version", "Версия согласия"),
    ("consent_at", "Дата согласия"),
    ("notified_at", "Уведомление отправлено"),
]


def export_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    stamp = timezone.localtime().strftime("%Y-%m-%d")
    response["Content-Disposition"] = f'attachment; filename="zayavki-{stamp}.csv"'
    response.write("﻿")  # BOM для Excel

    writer = csv.writer(response, delimiter=";")
    writer.writerow([title for _, title in COLUMNS])

    queryset = FormSubmission.objects.select_related("house").order_by("-created_at")
    for item in queryset:
        row = []
        for field, _ in COLUMNS:
            value = getattr(item, field, "")
            if field == "form_type":
                value = item.get_form_type_display()
            elif field == "status":
                value = item.get_status_display()
            elif field == "house":
                value = item.house.title if item.house else ""
            elif field == "consent_given":
                value = "да" if item.consent_given else "нет"
            elif hasattr(value, "strftime"):
                value = timezone.localtime(value).strftime("%d.%m.%Y %H:%M") if field.endswith("_at") else value.strftime("%d.%m.%Y")
            row.append(value if value is not None else "")
        writer.writerow(row)

    return response
