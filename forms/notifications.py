"""Уведомления о заявках — п. 7 ТЗ: Telegram и email не позже минуты.

Отправляем синхронно, сразу после сохранения заявки. Очередь задач
(Celery и подобное) здесь не заводится намеренно: она требует брокера
и второго процесса, а на Amvera приложение живёт одним контейнером.
Ради двух коротких HTTP-запросов усложнять развёртывание не стоит —
это ударило бы по требованию п. 10.15 о простоте передачи проекта.

Заявка сохраняется ДО отправки. Если Telegram или почта недоступны,
уведомление просто не уйдёт, но данные гостя не потеряются, и заявку
будет видно в админке.
"""

import logging

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)

# Короткий таймаут: гость ждёт ответа страницы, и внешний сервис
# не должен подвешивать отправку формы.
TIMEOUT_SECONDS = 5


def _lines(submission):
    rows = [
        f"Заявка: {submission.get_form_type_display()}",
        f"Имя: {submission.name}",
    ]
    if submission.phone:
        rows.append(f"Телефон: {submission.phone}")
    if submission.email:
        rows.append(f"Почта: {submission.email}")
    if submission.house:
        rows.append(f"Дом: {submission.house.title}")
    if submission.date_from:
        rows.append(f"Заезд: {submission.date_from:%d.%m.%Y}")
    if submission.date_to:
        rows.append(f"Выезд: {submission.date_to:%d.%m.%Y}")
    if submission.guests:
        rows.append(f"Гостей: {submission.guests}")
    if submission.message:
        rows.append(f"Сообщение: {submission.message}")
    if submission.source_url:
        rows.append(f"Страница: {submission.source_url}")
    if submission.utm_source:
        rows.append(f"Источник: {submission.utm_source} / {submission.utm_medium}")
    return rows


def send_telegram(submission):
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        logger.info("Telegram не настроен, уведомление пропущено")
        return False

    text = "\n".join(_lines(submission))
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return True
    except Exception:
        # Ловим всё подряд намеренно: заявка уже сохранена, и никакая
        # неполадка на стороне мессенджера не должна уронить ответ гостю.
        # Он увидит «заявка принята», а владелец найдёт её в админке.
        logger.exception("Не удалось отправить уведомление в Telegram")
        return False


def send_service_message(text):
    """Служебное сообщение владельцу — не о заявке, а о состоянии сайта.

    Пока используется для сбоя виджета бронирования (п. 5.6.4 ТЗ).
    """
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        logger.info("Telegram не настроен, служебное сообщение пропущено")
        return False

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return True
    except Exception:
        logger.exception("Не удалось отправить служебное сообщение в Telegram")
        return False


def send_email(submission):
    recipient = getattr(settings, "NOTIFY_EMAIL", "")
    if not recipient:
        logger.info("Адрес для уведомлений не задан, письмо пропущено")
        return False

    subject = f"Заявка с сайта: {submission.get_form_type_display()}"
    try:
        send_mail(
            subject=subject,
            message="\n".join(_lines(submission)),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception("Не удалось отправить письмо с заявкой")
        return False


def notify(submission):
    """Отправляет оба уведомления и отмечает время, если хоть одно ушло."""
    sent_telegram = send_telegram(submission)
    sent_email = send_email(submission)

    if sent_telegram or sent_email:
        submission.notified_at = timezone.now()
        submission.save(update_fields=["notified_at"])

    return sent_telegram, sent_email
