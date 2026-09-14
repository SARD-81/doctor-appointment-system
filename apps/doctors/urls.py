from django.urls import path

from apps.doctors import views

app_name = "doctors"

urlpatterns = [
    path("", views.doctor_list_view, name="list"),
    path("<int:doctor_id>/", views.doctor_detail_view, name="detail"),
]
