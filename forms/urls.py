from django.urls import path

from . import views

app_name = "forms"

urlpatterns = [
    # Тип формы в адресе: одна вьюха обслуживает все пять форм,
    # набор полей определяется классом формы.
    path("zayavka/<slug:form_type>/", views.submit, name="submit"),
    # Сигнал о недоступности виджета Контура — п. 5.6.4 ТЗ.
    path("sboy-vidzheta/", views.widget_error, name="widget_error"),
]
