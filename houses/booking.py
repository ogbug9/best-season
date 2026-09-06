"""Календарь и расчёт стоимости для блока бронирования на странице дома.

Источник данных отделён от всего остального намеренно. Сегодня цены
берутся из админки (`HousePage.price_per_night` и сезонные правила),
завтра — из API Контур.Отеля. Шаблон, CSS и скрипт разговаривают только
с функциями этого модуля и с двумя endpoint'ами, поэтому подключение PMS
не тронет ни разметку, ни вёрстку.

Считаем на сервере: сумма, которую видит гость, не должна зависеть от
того, что подставит в JS браузер.
"""

import calendar
from datetime import date, timedelta

from django.utils.dates import MONTHS
from django.utils.timezone import localdate

# Пределы диапазона. Минимум — ночь: бронь «заезд и выезд в один день»
# в PMS не существует. Максимум держим человеческим, длинные брони
# заводятся вручную через заявку.
MIN_NIGHTS = 1
MAX_NIGHTS = 60

# Сколько месяцев показывает панель. В макете их два, рядом.
MONTHS_SHOWN = 2

# Насколько далеко вперёд можно листать календарь.
MAX_MONTHS_AHEAD = 12


class NotConfigured(Exception):
    """Источник данных не настроен — работаем на локальных ценах."""


class LocalProvider:
    """Цены из админки, все даты свободны.

    Занятость сайту неоткуда взять до подключения PMS, и показывать
    выдуманную «занятость» хуже, чем не показывать никакой: гость
    поверит и уйдёт. Поэтому дни просто свободны, а окончательную
    доступность подтверждает виджет Контура.
    """

    def nightly_price(self, house, day):
        return house.nightly_price(day)

    def is_available(self, house, day):
        return True


class KonturProvider(LocalProvider):
    """Остатки и цены из Контур.Отеля.

    Подключается, когда будут доступы к API кабинета: пока в настройках
    есть только hotelId для виджета, а он остатки не отдаёт.
    """

    def __init__(self, hotel_id):
        raise NotConfigured("API Контура ещё не подключено")


def get_provider(house=None):
    return LocalProvider()


def _today():
    return localdate()


def _parse(value):
    """Дата из строки `ГГГГ-ММ-ДД`. Мусор молча превращается в None:
    параметры приходят из адресной строки, и падать на них незачем."""
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def month_start(value=None):
    """Первое число месяца, с которого начинается календарь."""
    day = _parse(value) or _today()
    first = day.replace(day=1)
    today_first = _today().replace(day=1)
    # Назад в прошлое не листаем, слишком далеко вперёд — тоже
    if first < today_first:
        return today_first
    limit = _shift_month(today_first, MAX_MONTHS_AHEAD)
    return min(first, limit)


def _shift_month(first, delta):
    month = first.month - 1 + delta
    return date(first.year + month // 12, month % 12 + 1, 1)


def calendar_months(house, start=None, months=MONTHS_SHOWN, selection=None):
    """Сетка календаря на несколько месяцев.

    Возвращает список месяцев; в каждом — недели по семь ячеек, неделя
    начинается с понедельника. Дни соседних месяцев не выбрасываем, а
    помечаем `outside`: в макете они показаны бледными, а не пустыми.
    """
    first = month_start(start)
    provider = get_provider(house)
    today = _today()
    date_from, date_to = _range(selection)

    result = []
    for offset in range(months):
        current = _shift_month(first, offset)
        result.append(
            {
                "year": current.year,
                "month": current.month,
                "title": f"{MONTHS[current.month]} {current.year}",
                "iso": current.isoformat(),
                "weeks": _weeks(house, provider, current, today, date_from, date_to),
            }
        )

    prev_month = _shift_month(first, -1)
    next_month = _shift_month(first, months)
    return {
        "months": result,
        "start": first.isoformat(),
        "prev": prev_month.isoformat() if prev_month >= today.replace(day=1) else "",
        "next": (
            next_month.isoformat()
            if next_month <= _shift_month(today.replace(day=1), MAX_MONTHS_AHEAD)
            else ""
        ),
    }


def _weeks(house, provider, first, today, date_from, date_to):
    weeks = []
    # Календарь Python по умолчанию начинает неделю с понедельника —
    # это же и в макете («Пн Вт Ср Чт Пт Сб Вс»).
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(first.year, first.month):
        cells = []
        for day in week:
            cells.append(
                {
                    "date": day,
                    "iso": day.isoformat(),
                    "day": day.day,
                    "outside": day.month != first.month,
                    "past": day < today,
                    "today": day == today,
                    "available": day >= today and provider.is_available(house, day),
                    "price": provider.nightly_price(house, day),
                    "selected": day in (date_from, date_to),
                    "in_range": bool(
                        date_from and date_to and date_from < day < date_to
                    ),
                    # Края полосы: по ним CSS скругляет подсветку
                    # диапазона, иначе она обрубается посреди ячейки.
                    "range_start": bool(date_to and day == date_from),
                    "range_end": bool(date_from and day == date_to),
                }
            )
        weeks.append(cells)
    return weeks


def _range(selection):
    """Пара дат из чего угодно: словаря, кортежа или None."""
    if not selection:
        return None, None
    if isinstance(selection, dict):
        return _parse(selection.get("date_from")), _parse(selection.get("date_to"))
    date_from, date_to = selection
    return _parse(date_from), _parse(date_to)


def quote(house, date_from=None, date_to=None, adults=None, children=0, pets=0):
    """Итог для правой карточки: ночей, гостей, сумма.

    Пока даты не выбраны, суммы нет — показывается цена «от». Ошибку
    отдаём текстом, чтобы её можно было показать и в шаблоне, и в JSON,
    не расходясь формулировками.
    """
    date_from = _parse(date_from)
    date_to = _parse(date_to)
    adults = _clamp(adults, 1, house.max_adults, default=min(2, house.max_adults))
    children = _clamp(children, 0, house.max_children, default=0)
    pets = _clamp(pets, 0, house.max_pets, default=0)

    result = {
        "date_from": date_from.isoformat() if date_from else "",
        "date_to": date_to.isoformat() if date_to else "",
        "adults": adults,
        "children": children,
        "pets": pets,
        "guests": adults + children,
        "nights": 0,
        "total": None,
        "price_from": house.price_per_night or house.price_from or 0,
        "error": "",
    }

    if not (date_from and date_to):
        return result

    nights = (date_to - date_from).days
    if nights < MIN_NIGHTS:
        result["error"] = "Дата выезда должна быть позже даты заезда."
        return result
    if nights > MAX_NIGHTS:
        result["error"] = f"Максимальный срок — {MAX_NIGHTS} ночей."
        return result
    if date_from < _today():
        result["error"] = "Заезд не может быть в прошлом."
        return result
    if adults + children > house.capacity:
        result["error"] = f"В домике размещается до {house.capacity} гостей."
        return result

    provider = get_provider(house)
    total = 0
    for offset in range(nights):
        day = date_from + timedelta(days=offset)
        if not provider.is_available(house, day):
            result["error"] = "Часть выбранных дат занята."
            return result
        total += provider.nightly_price(house, day)

    result["nights"] = nights
    result["total"] = total + pets * house.pet_fee
    return result


def _clamp(value, low, high, default):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(number, high))


def nights_label(nights):
    """«1 ночь», «2 ночи», «5 ночей» — русские окончания."""
    return _plural(nights, "ночь", "ночи", "ночей")


def guests_label(guests):
    return _plural(guests, "гость", "гостя", "гостей")


def _plural(number, one, few, many):
    tail = number % 100
    if 11 <= tail <= 14:
        word = many
    elif number % 10 == 1:
        word = one
    elif 2 <= number % 10 <= 4:
        word = few
    else:
        word = many
    return f"{number} {word}"
