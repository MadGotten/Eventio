from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.base import ContentFile


def validate_image(image, size=(500, 300)):
    img = Image.open(image)
    img.verify()
    img = Image.open(image)

    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")

    img = ImageOps.contain(img, size)
    temp_img = BytesIO()
    img.save(temp_img, format="WEBP", optimize=True, quality=95)
    temp_img.seek(0)
    return ContentFile(temp_img.read())
