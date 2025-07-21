from django.conf import settings
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from events.models import Event, Registration, Purchase, Ticket, Review
from django.db.utils import IntegrityError
from django.db import transaction
import uuid
from PIL import Image
import io


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user")
        self.user2 = User.objects.create(username="user2")
        self.super_user = User.objects.create(username="superuser", is_staff=True)

        self.mock_image = SimpleUploadedFile(
            name="test_image.jpg",
            content=self.create_test_image().getvalue(),
            content_type="image/jpeg",
        )

        self.event = Event.objects.create(
            title="Test Event",
            description="Event Description",
            location="Test Location",
            date=timezone.now(),
            banner=self.mock_image,
            created_by=self.user,
        )

    def tearDown(self):
        self.user.delete()
        self.user2.delete()
        self.super_user.delete()
        self.event.delete()

    def create_test_image(self, mode="RGB", format="JPEG"):
        image = Image.new(mode, (100, 100), color="red")
        temp_img = io.BytesIO()
        image.save(temp_img, format=format)
        temp_img.seek(0)
        return temp_img

    def test_event_creation(self):
        self.assertTrue(isinstance(self.event.id, uuid.UUID))
        self.assertEqual(self.event.title, "Test Event")
        self.assertEqual(self.event.description, "Event Description")
        self.assertEqual(self.event.location, "Test Location")
        self.assertEqual(self.event.created_by, self.user)
        self.assertEqual(self.event.event_type, "free")
        self.assertTrue(isinstance(self.event.date, timezone.datetime))

    def test_event_str_method(self):
        self.assertEqual(str(self.event), "Test Event")

    def test_event_is_free_property(self):
        self.assertTrue(self.event.is_free)
        self.assertFalse(self.event.is_paid)

    def test_event_is_paid_property(self):
        self.event.event_type = "paid"
        self.assertTrue(self.event.is_paid)
        self.assertFalse(self.event.is_free)

    def test_is_allowed_to_view(self):
        self.assertTrue(self.event.is_allowed_to_view(self.user))
        self.assertTrue(self.event.is_allowed_to_view(self.super_user))
        self.assertFalse(self.event.is_allowed_to_view(self.user2))

    def test_get_absolute_url(self):
        self.assertEqual(self.event.get_absolute_url(), f"/event/{self.event.id}/")

    def test_image_is_saved_as_webp(self):
        self.assertTrue(self.event.banner.name.endswith(".webp"))

    def test_upload_same_image(self):
        temp_name = self.event.banner.name
        self.event.banner = self.event.banner
        self.event.save()

        self.assertEqual(self.event.banner.name, temp_name)

    def test_diffrent_img_mode(self):
        test_image = SimpleUploadedFile(
            name="test_image.png",
            content=self.create_test_image(mode="RGBA", format="PNG").getvalue(),
            content_type="image/png",
        )
        self.event.banner = test_image
        self.event.save()

        with open(self.event.banner.path, "rb") as image_file:
            img = Image.open(image_file)
            img_mode = img.mode

        self.assertTrue(self.event.banner.name.endswith(".webp"))
        self.assertEqual(img_mode, "RGB")

    def test_invalid_image_upload(self):
        invalid_image = SimpleUploadedFile(
            name="test.txt", content=b"Invalid content", content_type="text/plain"
        )

        event = Event(
            title="Invalid Image Event",
            description="Invalid image description",
            location="Invalid Location",
            date=timezone.now(),
            banner=invalid_image,
            created_by=self.user,
        )

        with self.assertRaises(ValueError):
            event.save()

    def test_event_status_default(self):
        self.assertEqual(self.event.status, "pending")

    def test_get_banner_url_returns_none_if_no_banner(self):
        event = Event.objects.create(
            title="Test Event",
            description="Event Description",
            location="Test Location",
            date=timezone.now(),
            banner=None,
            created_by=self.user,
        )

        self.assertIsNone(event.get_banner_url())

    def test_get_banner_url_returns_banner_url(self):
        self.assertEqual(self.event.get_banner_url(), settings.STATIC_HOST + self.event.banner.url)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class RegistrationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user")
        self.user2 = User.objects.create(username="user2")

        self.event = Event.objects.create(
            title="Test Event",
            description="Event Description",
            location="Test Location",
            date=timezone.now(),
            created_by=self.user,
        )
        self.registration = Registration.objects.create(user=self.user, event=self.event)

    def tearDown(self):
        self.user.delete()
        self.user2.delete()
        self.event.delete()
        self.registration.delete()

    def test_registration_creation(self):
        self.assertEqual(self.registration.user, self.user)
        self.assertEqual(self.registration.event, self.event)
        self.assertTrue(isinstance(self.registration.registered_at, timezone.datetime))

    def test_registration_str_method(self):
        self.assertEqual(
            str(self.registration), f"{self.user.username} registered for {self.event.title}"
        )

    def test_unique_user_event_registration(self):
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Registration.objects.create(user=self.user, event=self.event)

    def test_different_users_can_register_for_same_event(self):
        registration2 = Registration.objects.create(user=self.user2, event=self.event)
        self.assertEqual(registration2.user, self.user2)
        self.assertEqual(registration2.event, self.event)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class PurchaseModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user")
        self.event = Event.objects.create(
            title="Test Event",
            description="Event Description",
            location="Test Location",
            date=timezone.now(),
            created_by=self.user,
        )
        self.ticket = Ticket.objects.create(price=10, quantity=1, event=self.event)
        self.purchase = Purchase.objects.create(
            user=self.user,
            ticket=self.ticket,
            quantity=1,
            event_name=self.event.title,
            amount_paid=self.ticket.price_to_cents,
        )

    def tearDown(self):
        self.user.delete()
        self.event.delete()
        self.ticket.delete()
        self.purchase.delete()

    def test_purchase_creation(self):
        self.assertEqual(self.purchase.user, self.user)
        self.assertEqual(self.purchase.ticket, self.ticket)
        self.assertEqual(self.purchase.quantity, 1)
        self.assertEqual(self.purchase.event_name, self.event.title)
        self.assertEqual(self.purchase.amount_paid, self.ticket.price_to_cents)
        self.assertTrue(isinstance(self.purchase.purchased_at, timezone.datetime))

    def test_purchase_str_method(self):
        self.assertEqual(
            str(self.purchase), f"{self.user.username} bought ticket for {self.ticket.event.title}"
        )

    def test_purchase_total_property_formats_correct(self):
        self.assertTrue(isinstance(self.purchase.total, str))
        self.assertEqual(self.purchase.total, "10.00")

    def test_purchase_total_property_formats_correct_with_arbitrary_amount(self):
        self.purchase.amount_paid = 583021
        self.assertTrue(isinstance(self.purchase.total, str))
        self.assertEqual(self.purchase.total, "5830.21")

    # def test_purchase_total_property_with_quantity_7(self):
    #    self.purchase.quantity = 7
    #    self.assertEqual(self.purchase.total, 70)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user")
        self.event = Event.objects.create(
            title="Test Event",
            description="Event Description",
            location="Test Location",
            date=timezone.now(),
            created_by=self.user,
        )
        self.review = Review.objects.create(
            user=self.user, event=self.event, rating=5, comment="Good"
        )

    def tearDown(self):
        self.user.delete()
        self.event.delete()

    def test_review_str_return(self):
        self.assertEqual(
            str(self.review),
            f"Review by {self.user.username} for {self.event.title} - {self.review.rating}",
        )


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class TicketModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user")
        self.event = Event.objects.create(
            title="Test Event",
            description="Event Description",
            location="Test Location",
            date=timezone.now(),
            created_by=self.user,
        )
        self.ticket = Ticket.objects.create(price=10, quantity=10, event=self.event)

    def tearDown(self):
        self.user.delete()
        self.ticket.delete()

    def test_ticket_property_price_to_cents(self):
        self.ticket.price = 42.21
        self.assertEqual(self.ticket.price_to_cents, 4221)

    def test_ticket_buy_method_with_quantity_of_1(self):
        self.ticket.buy(self.user, self.event, 1)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.quantity, 9)
        self.assertEqual(self.ticket.purchase_set.count(), 1)
        self.assertEqual(self.ticket.purchase_set.first().user, self.user)

    def test_ticket_buy_method_with_quantity_4(self):
        self.ticket.buy(self.user, self.event, 4)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.quantity, 6)
        self.assertEqual(self.ticket.purchase_set.count(), 1)
        self.assertEqual(self.ticket.purchase_set.first().user, self.user)
