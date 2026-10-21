from django.urls import path

from . import views

app_name = "houses"

urlpatterns = [
    # Домик в адресе слагом: страницы домов лежат в дереве Wagtail, и
    # у них нет собственных числовых id, на которые можно сослаться.
    path("api/domik/<slug:slug>/kalendar/", views.calendar, name="calendar"),
    path("api/domik/<slug:slug>/raschet/", views.price, name="price"),
]
