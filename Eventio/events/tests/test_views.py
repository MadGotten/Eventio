from django.test import TestCase, override_settings, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from events.models import Event


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ReviewViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user")
        self.event = Event.objects.create(
            title="Test Event",
            description="Event Description",
            location="Test Location",
            date=timezone.now(),
            created_by=self.user,
        )
        self.client = Client()
        self.client.force_login(self.user)

    def tearDown(self):
        self.user.delete()
        self.event.delete()

    def test_create_review_returns_created_response(self):
        response = self.client.post(
            reverse("review_create", kwargs={"pk": self.event.id}),
            {"rating": 5, "comment": "Good"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.context["review"].rating, 5)
        self.assertEqual(response.context["review"].comment, "Good")
        self.assertTemplateUsed(response, "partials/_review.html")

    def test_create_review_returns_redirect_to_login_page_response_for_logout_user(self):
        self.client.logout()
        response = self.client.post(
            reverse("review_create", kwargs={"pk": self.event.id}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f"{reverse("account_login")}?next={reverse('event_detail', kwargs={'pk': self.event.id})}review/",
            fetch_redirect_response=False,
        )

    def test_create_review_returns_redirect_for_bad_review_form_validation(self):
        response = self.client.post(
            reverse("review_create", kwargs={"pk": self.event.id}),
            {"rating": 8, "comment": "Good"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("event_detail", kwargs={"pk": self.event.id}),
            fetch_redirect_response=False,
        )
