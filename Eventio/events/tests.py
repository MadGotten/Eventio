from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from events.models import Event, Registration
from django.db.utils import IntegrityError
from django.db import transaction
import uuid
from PIL import Image
import io


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.super_user = User.objects.create(username="superuser", is_staff=True)
        self.second_user = User.objects.create(username="secondtestuser")

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
        self.super_user.delete()
        self.second_user.delete()
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

    def test_is_allowed_to_view(self):
        self.assertTrue(self.event.is_allowed_to_view(self.user))
        self.assertTrue(self.event.is_allowed_to_view(self.super_user))
        self.assertFalse(self.event.is_allowed_to_view(self.second_user))

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


class RegistrationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.second_user = User.objects.create(username="seconduser")

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
        self.second_user.delete()
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
        registration2 = Registration.objects.create(user=self.second_user, event=self.event)
        self.assertEqual(registration2.user, self.second_user)
        self.assertEqual(registration2.event, self.event)
