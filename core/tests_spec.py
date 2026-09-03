"""Соответствие вёрстки реестру измеренных значений макета.

Зачем это тест, а не отдельный скрипт: значения из design/spec.json
легко сломать случайно — правишь один селектор, а он перебивает другой.
Без теста это заметит заказчик, а не разработчик, и именно так уже
происходило.

Полная проверка требует браузера (вычисленные стили доступны только
в нём) и запущенного сервера — она живёт в design/check_spec.py и
гоняется отдельно. Здесь проверяется то, что можно проверить без
браузера, но что ловит подавляющее большинство поломок:

  1. Реестр не потерял подтверждённые значения
  2. Каждое значение из реестра встречается в CSS
  3. Правила проекта, нарушение которых стоит дорого

Тест намеренно не проверяет вычисленные стили: это дало бы ложную
уверенность. Он проверяет, что значение вообще есть в исходниках, —
дальше слово за design/check_spec.py.
"""

import json
import re
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "design/spec.json").read_text(encoding="utf-8"))
CSS = (ROOT / "config/static/css/main.css").read_text(encoding="utf-8")

# Источники, которые считаются фактом. Всё остальное — догадка.
FACT_SOURCES = {"inspector", "reference", "derived", "requirement"}


def css_without_comments(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


CSS_CODE = css_without_comments(CSS)


class RegistryIntegrityTests(SimpleTestCase):
    """Реестр не должен деградировать: подтверждённые значения не
    превращаются обратно в догадки, а source не исчезает."""

    def test_every_value_has_source(self):
        missing = []
        for group in ("tokens",):
            for name, meta in SPEC[group].items():
                if "source" not in meta:
                    missing.append(f"{group}.{name}")
        for comp, data in SPEC["components"].items():
            for prop, meta in data["props"].items():
                if "source" not in meta:
                    missing.append(f"{comp}.{prop}")
        self.assertFalse(
            missing,
            "Без source невозможно отличить замер от догадки: " + ", ".join(missing),
        )

    def test_sources_are_known(self):
        allowed = FACT_SOURCES | {"assumed"}
        bad = []
        for comp, data in SPEC["components"].items():
            for prop, meta in data["props"].items():
                if meta["source"] not in allowed:
                    bad.append(f"{comp}.{prop} = {meta['source']}")
        self.assertFalse(bad, "Неизвестный тип источника: " + ", ".join(bad))

    def test_confirmed_values_did_not_shrink(self):
        """Сколько значений подтверждено замером.

        Число только растёт. Если тест упал — значит подтверждённое
        значение пометили как догадку или удалили. Это откат назад,
        и он должен быть осознанным: тогда правится и порог.
        """
        confirmed = sum(
            1
            for data in SPEC["components"].values()
            for meta in data["props"].values()
            if meta["source"] in FACT_SOURCES
        )
        self.assertGreaterEqual(
            confirmed, 76,
            f"Подтверждённых значений стало {confirmed}, было 76. "
            "Замеры не должны пропадать.",
        )

    def test_registry_has_no_guesses_left(self):
        """С 03.09 в реестре не осталось ни одной догадки — каждое
        значение снято инспектором, измерено с эталона или вычислено
        из замера. Пока это так, про соответствие макету можно говорить
        без оговорок.

        Если тест упал — в реестр добавили новый компонент, значения
        которого подобраны на глаз. Это допустимо как промежуточный шаг,
        но тогда правится и этот тест: тихо вернуться к догадкам нельзя.
        """
        guesses = [
            f"{comp}.{prop}"
            for comp, data in SPEC["components"].items()
            for prop, meta in data["props"].items()
            if meta["source"] == "assumed"
        ]
        self.assertFalse(
            guesses,
            "В реестре снова появились догадки: " + ", ".join(guesses)
            + ". Запросите скриншот инспектора по этим узлам.",
        )

    def test_assumptions_are_labelled(self):
        """У каждой догадки должно быть написано, чего именно не хватает.
        Догадка без пояснения через неделю неотличима от замера."""
        silent = [
            f"{comp}.{prop}"
            for comp, data in SPEC["components"].items()
            for prop, meta in data["props"].items()
            if meta["source"] == "assumed" and not meta.get("заметка")
        ]
        self.assertFalse(
            silent, "Догадка без пояснения: " + ", ".join(silent)
        )


class CssMatchesRegistryTests(SimpleTestCase):
    """Значения, подтверждённые замером, обязаны присутствовать в CSS.

    Это грубая проверка «значение вообще есть в исходниках». Точную
    сверку вычисленных стилей делает design/check_spec.py в браузере.
    """

    def assert_in_css(self, needle, why):
        self.assertIn(
            needle.lower(), CSS_CODE.lower(),
            f"{why}: значение {needle} не найдено в main.css. "
            "Либо вёрстка разошлась с design/spec.json, либо значение "
            "задано иначе — тогда поправьте и реестр, и этот тест.",
        )

    def test_palette_present(self):
        for key in ("color.cream", "color.olive", "color.terra",
                    "color.dark", "color.deep"):
            self.assert_in_css(SPEC["tokens"][key]["value"],
                               f"цвет палитры {key}")

    def test_hero_height_from_reference(self):
        self.assert_in_css("877px", "высота первого экрана, замер по эталону")

    def test_section_title_size(self):
        self.assert_in_css("5.625rem", "заголовок секции 90px = 5.625rem")

    def test_container_width(self):
        """1240px — по инспектору, три независимые секции с Left 100px.
        Значение 1360px, стоявшее здесь раньше, было снято с выгрузки
        всех слоёв и оказалось шире макета на 120px."""
        self.assert_in_css("1240px", "ширина контейнера")
        self.assertNotIn("1360px", CSS_CODE,
                         "Вернулась старая ширина контейнера 1360px — "
                         "страница снова шире макета на 120px")

    def test_vertical_rhythm(self):
        """Шаг между секциями и внутри секции — из инспектора, а не на глаз."""
        self.assert_in_css("--section-gap-outer: 120px", "шаг между секциями")
        self.assert_in_css("--section-gap-inner: 60px", "зазор заголовок→контент")

    def test_radius_scale(self):
        for value in ("10px", "20px", "100px"):
            self.assert_in_css(value, "шкала скруглений")


class ProjectRulesTests(SimpleTestCase):
    """Правила, нарушение которых стоит дороже, чем расхождение с макетом."""

    def test_no_global_reset(self):
        """Контур официально снимает поддержку при глобальных `* {}`
        и `div {}` — см. 03-kontur-widget.md. Ошибка на один символ
        здесь обходится дороже любой вёрстки."""
        for line in CSS.splitlines():
            s = line.strip()
            self.assertFalse(s.startswith("* {"), f"Глобальный сброс: {s}")
            self.assertFalse(s.startswith("div {"), f"Голый div: {s}")
            self.assertFalse(s.startswith("*,"), f"Глобальный сброс: {s}")

    def test_box_sizing_is_scoped_not_global(self):
        """box-sizing на html без `*` не наследуется — на этом уже
        ловились: кнопка с width:100% и полями 40px вылезала за экран.
        Правило должно быть скоуплено под .site."""
        self.assertIn("box-sizing: border-box", CSS_CODE)
        self.assertIn(".site :where(div, section", CSS_CODE,
                      "Скоупленное правило box-sizing пропало — вернётся "
                      "горизонтальная прокрутка")

    def test_olive_not_used_for_small_text(self):
        """Оливковый на кремовом даёт 3.6. Это годится только для
        крупного текста (от 18.66px при весе 700). Для обычного нужен
        затемнённый #746F4C.

        Проверяем косвенно: затемнённый вариант обязан присутствовать —
        значит про ограничение помнили.
        """
        self.assertIn("#746F4C".lower(), CSS_CODE.lower(),
                      "Пропал затемнённый оливковый для мелкого текста. "
                      "Контраст 15px кремового на #847F57 = 3.6 при норме 4.5")

    def test_hero_title_has_scrim(self):
        """Заголовок первого экрана оливковый — как в макете. На нашем
        фоне это 2.81, ниже порога 3.0 даже для крупного текста.
        Читаемость держится на затемнении, и оно не должно исчезнуть
        при следующей правке."""
        self.assertIn(".hero::before", CSS_CODE,
                      "Пропало затемнение под текстом первого экрана — "
                      "оливковый заголовок перестанет проходить по контрасту")

    def test_focus_is_always_visible(self):
        """П. 10.13 ТЗ: работа с клавиатуры. Видимый фокус убирать нельзя."""
        self.assertIn("focus-visible", CSS_CODE)
        self.assertNotIn("outline: none", CSS_CODE.replace(" ", " "))
