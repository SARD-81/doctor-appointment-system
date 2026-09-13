import pytest
from django.urls import reverse

from apps.reviews.models import Review
from apps.reviews.services import ReviewService


@pytest.mark.django_db
class TestCreateReviewView:
    def url(self, appointment):
        return reverse("reviews:create", args=[appointment.pk])

    def test_anonymous_post_redirects_and_creates_nothing(self, client, completed_appointment):
        response = client.post(self.url(completed_appointment), {"rating": "5"})
        assert response.status_code == 302
        assert Review.objects.count() == 0

    def test_get_is_not_allowed(self, client, completed_appointment, patient):
        client.force_login(patient)
        response = client.get(self.url(completed_appointment))
        assert response.status_code == 405

    def test_owner_can_submit_review(self, client, completed_appointment, patient):
        client.force_login(patient)
        response = client.post(
            self.url(completed_appointment),
            {"rating": "5", "comment": "پزشک مهربان"},
            follow=True,
        )

        assert response.redirect_chain[-1][0] == reverse("appointments:my_appointments")
        assert Review.objects.count() == 1
        review = Review.objects.get()
        assert review.rating == 5
        assert review.comment == "پزشک مهربان"

    def test_other_owner_gets_404(self, client, completed_appointment, other_patient):
        client.force_login(other_patient)
        response = client.post(self.url(completed_appointment), {"rating": "5"})
        assert response.status_code == 404
        assert Review.objects.count() == 0

    def test_not_completed_appointment_redirects_with_error(
        self, client, confirmed_appointment, patient
    ):
        client.force_login(patient)
        response = client.post(
            self.url(confirmed_appointment), {"rating": "5"}, follow=True
        )

        assert response.redirect_chain[-1][0] == reverse("appointments:my_appointments")
        messages = list(response.context["messages"])
        assert any("تکمیل" in str(m) for m in messages)
        assert Review.objects.count() == 0

    def test_duplicate_review_redirects_with_error(self, client, completed_appointment, patient):
        ReviewService.create_review(
            patient=patient,
            appointment_id=completed_appointment.pk,
            rating=5,
        )
        client.force_login(patient)
        response = client.post(
            self.url(completed_appointment),
            {"rating": "4", "comment": "نظر دوم"},
            follow=True,
        )

        assert response.redirect_chain[-1][0] == reverse("appointments:my_appointments")
        messages = list(response.context["messages"])
        assert any("قبلا" in str(m) for m in messages)
        assert Review.objects.count() == 1

    def test_invalid_rating_redirects_with_error(self, client, completed_appointment, patient):
        client.force_login(patient)
        response = client.post(
            self.url(completed_appointment), {"rating": "9"}, follow=True
        )

        assert response.redirect_chain[-1][0] == reverse("appointments:my_appointments")
        messages = list(response.context["messages"])
        assert any("امتیاز" in str(m) for m in messages)
        assert Review.objects.count() == 0

    def test_comment_is_optional(self, client, completed_appointment, patient):
        client.force_login(patient)
        client.post(self.url(completed_appointment), {"rating": "5"})

        review = Review.objects.get()
        assert review.comment == ""
