# Фото: этапы 1–3, 01.10.2026

Рабочая база: `1b63ef9`. Относительно диагностической базы `cbce3e8` код фотографий не менялся; в `base.html` изменена только версия отдельного мобильного CSS. Подробного файла `claude/18-foto-kachestvo-01-10.md` в рабочей папке нет; использован присланный запрос.

Проверки выполняются локально с production-выдачей фото (`DEBUG=False`, `GENERATE_IMAGE_RENDITIONS_ON_REQUEST=False`), копией SQLite и существующими фотографиями. Сервер, настройки, логи и снимки — в `tmp/photo-quality-20261001/`; `config/settings/local.py` уже существовал и не изменялся. Python311 недоступен, использован bundled Python 3.12 с добавлением `.venv/Lib/site-packages` в конец `sys.path`.

## Этап 1 — кадр и фокус

1. `main.css`: ограничена grid-строка слайдов домов, `picture` получает высоту окна; фото галереи позиционируется внутри квадратной плитки. Добавлен scoped `object-position` через `--focus`, исключающий Контур. Затемнения не менялись.
2. `media_tags.py`: фокус Wagtail передаётся в обе ветки `<img>`. `base.html`: версия `20261001-photo-frame`. `core/tests.py`: проверка production-фокуса.
3. Полный набор Django: **108/108**, `manage.py check` и `git diff --check` успешны. Скрипт `check_images.py` создаётся на этапе 3.
4. Браузер: 1440×900/DPR1 и 390×844/DPR3, реальные файлы декодированы, шрифты загружены. Карточки на главной и в каталоге: 610×915 → **610×500**, на мобильном 350×525 → **350×287.38**. Галерея: **295×295** на десктопе и **165×165** на мобильном, `<img>` равен окну. «С мая по сентябрь»: **50% 94%**. Территория на десктопе: sports **50% 100%**, sauna **50% 72%**, river **50% 93%**. Ошибок JS, локальных ресурсов и горизонтального переполнения в проверенных состояниях нет.
5. Первый домик визуально сопоставлен с фрагментом `Desktop Main.png`: после правки показан тот же участок комнаты. Полный пиксельный аудит и численный замер L* этой сессией не выполнялись.

| Снимок | До | Этап 1 |
| --- | --- | --- |
| Главная, домик 1440 | [до](../tmp/photo-quality-20261001/before-home-card-1440.png) | [после](../tmp/photo-quality-20261001/stage-1-home-card-1440.png) |
| Главная, домик 390 | [до](../tmp/photo-quality-20261001/before-home-card-390.png) | [после](../tmp/photo-quality-20261001/stage-1-home-card-390.png) |
| Каталог, домик 1440 | [до](../tmp/photo-quality-20261001/before-houses-card-1440.png) | [после](../tmp/photo-quality-20261001/stage-1-houses-card-1440.png) |
| Каталог, домик 390 | [до](../tmp/photo-quality-20261001/before-houses-card-390.png) | [после](../tmp/photo-quality-20261001/stage-1-houses-card-390.png) |
| Галерея 390 | [до](../tmp/photo-quality-20261001/before-gallery-390.png) | [после](../tmp/photo-quality-20261001/stage-1-gallery-390.png) |
| «С мая по сентябрь» 1440 | [центрирование до](../tmp/photo-quality-20261001/before-promo-1440.png) | [фокус после](../tmp/photo-quality-20261001/stage-1-promo-1440.png) |
| «С мая по сентябрь» 390 | [центрирование до](../tmp/photo-quality-20261001/before-promo-390.png) | [фокус после](../tmp/photo-quality-20261001/stage-1-promo-390.png) |
| Герой 390@3x | [до](../tmp/photo-quality-20261001/before-hero-390.png) | [этап 1](../tmp/photo-quality-20261001/stage-1-hero-390.png) |

Снимки «до» нужной акции восстановлены с исходным центрированием через временный CSS `--focus:50% 50%`; файлы, размеры и production-режим те же. Остальные «до» сняты до правок. PNG сохранены в CSS-пикселях при указанной плотности браузера. [Измерения этапа 1](../tmp/photo-quality-20261001/stage-1-measurements.json), [фрагмент эталона](../tmp/photo-quality-20261001/reference-first-house.png).

Для этапов 2–3 материалы от владельца не нужны. Push и production-приёмка остаются владельцу после этапа 3.

Коммит этапа 1: `4b046c5` — `Photo stage 1: fix frames and pass Wagtail focal points`.

## Этап 2 — мобильный герой, srcset и preload

1. `media_tags.py`: `hero_mobile` — fill 9:19.5, запросы 640/828/1170, качество 82. Дескрипторы desktop/mobile используют реальные ширины без повторов. `_mobile_srcsets` общий для `<source>` и нового тега `mobile_srcset`. В `home_page.html` мобильный preload использует `imagesrcset`/`imagesizes`; desktop-preload сохранён.
2. `core/tests.py`: сброс rendition-кеша между тестами, портретный кроп, реальные ширины и отсутствие дублей в обеих ветках, совпадение production-preload/source без генерации в запросе.
3. Полный набор Django: **109/109**, `git diff --check` успешен. `prepare_mobile_images`: **60** спецификаций, выполнен на локальной копии базы. `run.py` уже вызывает эту команду; его менять не потребовалось.
4. Браузер: **9** состояний на 1440/DPR1 и 390/DPR3, без ошибок JS/локальных ресурсов/переполнения. Первый мобильный кадр **828×464 → 530×1148**, файл **185856 байт**, ровно **1** image-request к выбранному файлу; preload и WebP-source имеют одинаковый srcset. При DPR3 растяжение по высоте **5.46 → 2.21**: полностью резким исходник 2048×1148 стать не может.
5. Фактический результат **530**, а не примерные 532 px из запроса: это ширина готового Wagtail fill при соотношении 9:19.5. У ref-46 мобильные дескрипторы **360w/480w/736w**. У «С мая по сентябрь» редакторский `mobile_image` уже **360×220**; сохранён, srcset содержит один **360w**. Редакторские изображения и оригиналы не заменялись.
6. PageSpeed mobile (3 измерения, среднее ≥80) пока **не проверен**: новый код не опубликован, а измерение прежней версии не подтвердило бы эту правку. Production-приёмка и PageSpeed — после push владельцем. По текущей правке качество не подбиралось наугад.

Снимки этапа 2: [главная 1440](../tmp/photo-quality-20261001/stage-2-home-card-1440.png), [главная 390](../tmp/photo-quality-20261001/stage-2-home-card-390.png), [каталог 1440](../tmp/photo-quality-20261001/stage-2-houses-card-1440.png), [каталог 390](../tmp/photo-quality-20261001/stage-2-houses-card-390.png), [галерея 390](../tmp/photo-quality-20261001/stage-2-gallery-390.png), [акция 1440](../tmp/photo-quality-20261001/stage-2-promo-1440.png), [акция 390](../tmp/photo-quality-20261001/stage-2-promo-390.png), [герой 390@3x](../tmp/photo-quality-20261001/stage-2-hero-390.png). Снимки «до» — в таблице этапа 1. [Измерения этапа 2](../tmp/photo-quality-20261001/stage-2-measurements.json), [лог тестов](../tmp/photo-quality-20261001/stage-2-tests.log).

От владельца для этапа 3 ничего не требуется; следующий шаг — скрипт контроля и отчёт без push.

Коммит этапа 2: `c7b92f4` — `Photo stage 2: prepare portrait hero and correct srcset preload`.

## Этап 3 — контроль фотографий и остановка

1. Добавлен `design/check_images.py` с кодом из запроса: 12 маршрутов, 1440×900/DPR2 и 390×844/DPR3, реальные размеры файлов, порог растяжения ×1.15, проверка превышения окна.
2. Полный набор Django: **109/109**. Синтаксис Python и `git diff --check` успешны. Прямой запуск `python design/check_images.py` ограничен отсутствием Python-модуля `playwright` (`ModuleNotFoundError`); зависимости не устанавливались. Замер выполнен установленным Playwright Node и системным Edge: JavaScript `MEASURE`, маршруты, режимы и порог читаются непосредственно из Python-файла, агрегация повторяет его алгоритм. Внешние запросы блокировались, локальные страницы отдавали HTTP 200, ошибок JS и локальных ресурсов нет.
3. Результат **24** состояний: **обрезано сверху 0**, **растянуто 32**. Код выхода проверки **1** ожидаем из-за оставшихся слабых исходников. В показателе `up2` плотность намеренно нормирована к **2×** в обоих режимах, как в присланном скрипте; реальное DPR3-растяжение героя — ×2.21, а в выводе `up2` — ×1.47.
4. Снимки после этапа 3: [главная 1440](../tmp/photo-quality-20261001/stage-3-home-card-1440.png), [главная 390](../tmp/photo-quality-20261001/stage-3-home-card-390.png), [каталог 1440](../tmp/photo-quality-20261001/stage-3-houses-card-1440.png), [каталог 390](../tmp/photo-quality-20261001/stage-3-houses-card-390.png), [галерея 390](../tmp/photo-quality-20261001/stage-3-gallery-390.png), [акция 1440](../tmp/photo-quality-20261001/stage-3-promo-1440.png), [акция 390](../tmp/photo-quality-20261001/stage-3-promo-390.png), [герой 390@3x](../tmp/photo-quality-20261001/stage-3-hero-390.png). «До» — в таблице этапа 1. [Все замеры 12 страниц](../tmp/photo-quality-20261001/stage-3-measurements.json), [контрольные снимки/замеры](../tmp/photo-quality-20261001/stage-3-screens-measurements.json), [лог тестов](../tmp/photo-quality-20261001/stage-3-tests.log).
5. Остановлено после этапа 3. **Push/deploy не выполняются.** Владелец публикует и проверяет телефон/ноутбук/PageSpeed. Для этапов 4–5 нужны путь к папке оригиналов целиком и мобильный PNG «О нас»; для этапа 6 — решение о слайдах 2–3 героя и затемнении мобильной «О нас». Цветовой профиль, оригиналы, затемнения и редакторские фото в этой сессии не менялись; файл решений 07 остаётся владельцу.

Полный вывод контроля (эквивалентный запуск через Playwright Node):

```text
×3.05    945x2048 →  1440x900  десктоп 1440@2x   /                          /media/original_images/ref-28.webp
×2.5    1152x2048 →  1440x900  десктоп 1440@2x   /                          /media/original_images/ref-30.webp
×2.01     360x220 →   334x221  мобильный 390@3x  /akcii/                    /media/images/30a436e0f995.width-360.format-webp.webpquality-82.webp
×2        397x220 →   397x220  десктоп 1440@2x   /razmeshchenie/domik-1/    /media/original_images/review-60.webp
×2        397x220 →   397x220  десктоп 1440@2x   /razmeshchenie/domik-1/    /media/original_images/review-61.webp
×2        397x220 →   397x220  десктоп 1440@2x   /razmeshchenie/domik-1/    /media/original_images/review-62.webp
×2        397x220 →   397x220  десктоп 1440@2x   /razmeshchenie/domik-2/    /media/original_images/review-69.webp
×2        397x220 →   397x220  десктоп 1440@2x   /razmeshchenie/domik-2/    /media/original_images/review-70.webp
×2        397x220 →   397x220  десктоп 1440@2x   /razmeshchenie/domik-2/    /media/original_images/review-71.webp
×2        397x220 →   397x220  десктоп 1440@2x   /razmeshchenie/domik-3/    /media/original_images/review-77.webp
×2        397x220 →   397x220  десктоп 1440@2x   /razmeshchenie/domik-3/    /media/original_images/review-78.webp
×2        397x220 →   397x220  десктоп 1440@2x   /razmeshchenie/domik-3/    /media/original_images/review-79.webp
×2        397x220 →   397x220  десктоп 1440@2x   /razmeshchenie/domik-4/    /media/original_images/review-85.webp
×2        397x220 →   397x220  десктоп 1440@2x   /razmeshchenie/domik-4/    /media/original_images/review-86.webp
×2        397x220 →   397x220  десктоп 1440@2x   /razmeshchenie/domik-4/    /media/original_images/review-87.webp
×2        360x220 →   334x220  мобильный 390@3x  /akcii/                    /media/images/9cfd07d5bb93.width-360.format-webp.webpquality-82.webp
×1.91     639x960 →   610x500  десктоп 1440@2x   /                          /media/original_images/ref-81.webp
×1.78     685x960 →   610x500  десктоп 1440@2x   /                          /media/original_images/ref-64.webp
×1.78    686x1220 →   610x500  десктоп 1440@2x   /territoriya/uslugi/       /media/original_images/ref-06.webp
×1.77     586x880 →   518x647  десктоп 1440@2x   /                          /media/original_images/ref-31.webp
×1.73     525x700 →   455x455  десктоп 1440@2x   /                          /media/original_images/ref-29.webp
×1.69     720x960 →   610x500  десктоп 1440@2x   /                          /media/original_images/ref-63.webp
×1.69     720x960 →   610x500  десктоп 1440@2x   /                          /media/original_images/ref-72.webp
×1.57   2048x1148 →  1440x900  десктоп 1440@2x   /                          /media/original_images/ref-32.webp
×1.47    530x1148 →   390x844  мобильный 390@3x  /                          /media/images/ref-3.2e16d0ba.fill-640x1387.format-webp.webpquality-82.webp
×1.44    848x1055 →   610x500  десктоп 1440@2x   /razmeshchenie/            /media/original_images/ref-37.webp
×1.36    586x1300 →   390x886  мобильный 390@3x  /                          /static/img/home-about-mobile.webp
×1.33    1130x754 →   610x500  десктоп 1440@2x   /                          /media/original_images/ref-51.webp
×1.33     525x700 →   350x350  мобильный 390@3x  /                          /static/img/home-quote-mobile.webp
×1.18   1036x1500 →   610x500  десктоп 1440@2x   /territoriya/uslugi/       /media/original_images/ref-20.webp
×1.17    1280x852 →   610x500  десктоп 1440@2x   /                          /media/original_images/ref-73.webp
×1.17    1280x852 →   610x500  десктоп 1440@2x   /                          /media/original_images/ref-80.webp

Растянуто при плотности 2×: 32 (порог ×1.15)
Обрезано сверху: 0
```

Коммит этапа 3: `Photo stage 3: add photo quality checks and local verification report`; хеш — в финальном сообщении и `git log -1`.
