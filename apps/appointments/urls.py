from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("mine/", views.my_appointments_view, name="my_appointments"),
    path("success/<int:appointment_id>/", views.booking_success_view, name="booking_success"),
    path("book/<int:slot_id>/", views.book_appointment_view, name="book"),
]
