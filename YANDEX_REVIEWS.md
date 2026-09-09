# Яндекс: отзывы на главной

Данные предоставлены пользователем 09.09.2026. Интеграция пока не реализована: разрешено сохранить информацию, код сайта не менять.

## Организация

- Название: Лучший сезон
- ID: 3306085141
- Карточка: https://yandex.ru/maps/org/luchshiy_sezon/3306085141/
- Отзывы: https://yandex.ru/maps/org/luchshiy_sezon/3306085141/reviews/
- Короткая ссылка на карту: https://yandex.ru/maps/-/CTdxjD8f

## Требование

Разместить отзывы на главной после блока вопросов, перед футером. В переписке заказчика предпочтителен существующий дизайн отзывов со страницы домика, но допустим готовый виджет Яндекса для простой интеграции. Автоматическое получение данных для собственных карточек не подтверждено.

Предлагаемый следующий шаг после разрешения на реализацию: встроить официальный виджет отзывов, оформить заголовок и внешние отступы в стиле сайта, адаптировать ширину под мобильный экран. Внутренний дизайн виджета задаёт Яндекс. Конкретный виджет в браузере ещё не проверен.

## Виджет отзывов от пользователя

HTML очищен от экранирования и Markdown-обёрток ссылок в сообщении. Исходные размеры: 560 × 800 px.

```html
<div style="width:560px;height:800px;overflow:hidden;position:relative;">
  <iframe style="width:100%;height:100%;border:1px solid #e6e6e6;border-radius:8px;box-sizing:border-box" src="https://yandex.ru/maps-reviews-widget/3306085141?comments"></iframe>
  <a href="https://yandex.ru/maps/org/luchshiy_sezon/3306085141/" target="_blank" style="box-sizing:border-box;text-decoration:none;color:#b3b3b3;font-size:10px;font-family:YS Text,sans-serif;padding:0 20px;position:absolute;bottom:8px;width:100%;text-align:center;left:0;overflow:hidden;text-overflow:ellipsis;display:block;max-height:14px;white-space:nowrap;padding:0 16px;box-sizing:border-box">Лучший сезон на карте Тульской области — Яндекс Карты</a>
</div>
```

## Виджет карты от пользователя

Сохранён как справочный материал; добавление карты не поручено.

```html
<div style="position:relative;overflow:hidden;">
  <a href="https://yandex.ru/maps/org/luchshiy_sezon/3306085141/?utm_medium=mapframe&amp;utm_source=maps" style="color:#eee;font-size:12px;position:absolute;top:0px;">Лучший сезон</a>
  <a href="https://yandex.ru/maps/10832/tula-oblast/category/glamping/112956978208/?utm_medium=mapframe&amp;utm_source=maps" style="color:#eee;font-size:12px;position:absolute;top:14px;">Глэмпинг в Тульской области</a>
  <iframe src="https://yandex.ru/map-widget/v1/?ll=37.287677%2C54.725820&amp;mode=search&amp;oid=3306085141&amp;ol=biz&amp;z=15.53" width="560" height="400" frameborder="1" allowfullscreen="true" style="position:relative;"></iframe>
</div>
```

## Документация

https://yandex.ru/support/maps/ru/concept/get-map-reference

По справке, прочитанной 09.09.2026: для виджета отзывов поддерживается ширина 300–760 px, рекомендована высота не менее 500 px.
