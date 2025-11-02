# webchothuetro/sync_cloudinary.py
import os
import sys
import django
import traceback
from pathlib import Path

# ----- Ensure we run from project root -----
# Nếu chạy từ project root C:\pythonweb\webchothuetro
PROJECT_ROOT = Path(__file__).resolve().parent
# nếu bạn đặt file ở webchothuetro/ thì PROJECT_ROOT is that folder; muốn root project's parent
# but we expect this file to live inside webchothuetro/ per instructions, so base = parent
BASE_DIR = PROJECT_ROOT.parent  # project root

os.chdir(str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR))

# ----- DJANGO SETUP -----
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webchothuetro.settings")
django.setup()

from django.conf import settings
from cloudinary.uploader import upload as cloudinary_upload
from cloudinary.exceptions import Error as CloudinaryError

# import models after django.setup()
from app.models import (
    Product,
    ProductImage,
    ProductVideo,
    Video,
    DirectChatMessage,
)

MEDIA_DIR = Path(settings.MEDIA_ROOT)
print("🔎 Base dir:", BASE_DIR)
print("📂 Media dir:", MEDIA_DIR)
print("☁️ Cloudinary config:", getattr(settings, "CLOUDINARY_STORAGE", {}))
print()

def is_already_on_cloud(url_or_field):
    """Check if a file field value already points to Cloudinary remote."""
    if not url_or_field:
        return False
    s = str(url_or_field)
    return "res.cloudinary.com" in s or s.startswith("https://res.cloudinary.com")

def local_path_for(field_value):
    """Return absolute local filesystem path for a FileField / ImageField value."""
    if not field_value:
        return None
    # field_value may be a Django FieldFile -> str(field_value) gives relative path like 'products/x.png'
    rel = str(field_value)
    return MEDIA_DIR.joinpath(rel)

def safe_upload(local_path, resource_type="auto"):
    try:
        res = cloudinary_upload(str(local_path), resource_type=resource_type)
        return res
    except CloudinaryError as e:
        print("❌ Cloudinary upload error:", e)
        return None
    except Exception:
        print("❌ Unexpected upload error:")
        traceback.print_exc()
        return None

# -------------------
# Sync Product main image
# -------------------
print("=== Sync Product.image ===")
for p in Product.objects.all():
    try:
        val = p.image
        if not val:
            # no image
            continue
        url = getattr(val, "url", None)
        if is_already_on_cloud(url):
            print(f"· [{p.id}] {p.name}: already on cloud -> {url}")
            continue

        local = local_path_for(val)
        if not local or not local.exists():
            print(f"⚠️ [{p.id}] {p.name}: local file not found -> {local}")
            continue

        print(f"⬆️ [{p.id}] Uploading product image: {p.name} -> {local}")
        res = safe_upload(local, resource_type="image")
        if res and res.get("secure_url"):
            p.image = res["secure_url"]  # set to cloud URL (works if you want direct url stored)
            p.save(update_fields=["image"])
            print(f"✅ [{p.id}] Uploaded: {res['secure_url']}")
        else:
            print(f"❌ [{p.id}] Upload failed.")
    except Exception:
        print("❌ Error on product:", p.id, p.name)
        traceback.print_exc()

print()

# -------------------
# Sync ProductImage (related images)
# -------------------
print("=== Sync ProductImage.images ===")
for img in ProductImage.objects.select_related("product").all():
    try:
        val = img.image
        if not val:
            continue
        url = getattr(val, "url", None)
        if is_already_on_cloud(url):
            print(f"· Img[{img.id}] for Product[{img.product.id}] already on cloud.")
            continue
        local = local_path_for(val)
        if not local.exists():
            print(f"⚠️ Img[{img.id}] file not found: {local}")
            continue
        print(f"⬆️ Img[{img.id}] Uploading for Product[{img.product.id}]: {local}")
        res = safe_upload(local, resource_type="image")
        if res and res.get("secure_url"):
            img.image = res["secure_url"]
            img.save(update_fields=["image"])
            print(f"✅ Img[{img.id}] uploaded: {res['secure_url']}")
        else:
            print(f"❌ Img[{img.id}] upload failed.")
    except Exception:
        print("❌ Error on ProductImage:", img.id)
        traceback.print_exc()

print()

# -------------------
# Sync ProductVideo.video (resource_type=video)
# -------------------
print("=== Sync ProductVideo.video ===")
for vid in ProductVideo.objects.select_related("product").all():
    try:
        val = vid.video
        if not val:
            continue
        url = getattr(val, "url", None)
        if is_already_on_cloud(url):
            print(f"· Video[{vid.id}] already on cloud -> {url}")
            continue
        local = local_path_for(val)
        if not local.exists():
            print(f"⚠️ Video[{vid.id}] file not found: {local}")
            continue
        print(f"⬆️ Video[{vid.id}] Uploading for Product[{vid.product.id}]: {local}")
        res = safe_upload(local, resource_type="video")
        if res and res.get("secure_url"):
            vid.video = res["secure_url"]
            vid.save(update_fields=["video"])
            print(f"✅ Video[{vid.id}] uploaded: {res['secure_url']}")
        else:
            print(f"❌ Video[{vid.id}] upload failed.")
    except Exception:
        print("❌ Error on ProductVideo:", vid.id)
        traceback.print_exc()

print()

# -------------------
# Sync generic Video model (site videos)
# -------------------
print("=== Sync Video.file / thumbnail ===")
for v in Video.objects.all():
    try:
        # video file
        if v.file:
            url = getattr(v.file, "url", None)
            if not is_already_on_cloud(url):
                local = local_path_for(v.file)
                if local.exists():
                    print(f"⬆️ VideoModel[{v.id}] file -> {local}")
                    res = safe_upload(local, resource_type="video")
                    if res and res.get("secure_url"):
                        v.file = res["secure_url"]
                        v.save(update_fields=["file"])
                        print(f"✅ Uploaded video: {res['secure_url']}")
                else:
                    print(f"⚠️ VideoModel file not found: {local}")

        # thumbnail
        if v.thumbnail:
            url = getattr(v.thumbnail, "url", None)
            if not is_already_on_cloud(url):
                local = local_path_for(v.thumbnail)
                if local.exists():
                    print(f"⬆️ VideoModel[{v.id}] thumbnail -> {local}")
                    res = safe_upload(local, resource_type="image")
                    if res and res.get("secure_url"):
                        v.thumbnail = res["secure_url"]
                        v.save(update_fields=["thumbnail"])
                        print(f"✅ Uploaded thumbnail: {res['secure_url']}")
                else:
                    print(f"⚠️ VideoModel thumbnail not found: {local}")

    except Exception:
        print("❌ Error on Video model:", v.id)
        traceback.print_exc()

print()

# -------------------
# Sync DirectChatMessage images
# -------------------
print("=== Sync DirectChatMessage.image ===")
for m in DirectChatMessage.objects.all():
    try:
        if m.image:
            url = getattr(m.image, "url", None)
            if is_already_on_cloud(url):
                continue
            local = local_path_for(m.image)
            if not local.exists():
                print(f"⚠️ ChatImage[{m.id}] not found: {local}")
                continue
            print(f"⬆️ ChatImage[{m.id}] -> {local}")
            res = safe_upload(local, resource_type="image")
            if res and res.get("secure_url"):
                m.image = res["secure_url"]
                m.save(update_fields=["image"])
                print(f"✅ ChatImage[{m.id}] uploaded: {res['secure_url']}")
            else:
                print(f"❌ ChatImage[{m.id}] upload failed.")
    except Exception:
        print("❌ Error on DirectChatMessage:", m.id)
        traceback.print_exc()

print()
print("🎉 Done! All attempted media synced to Cloudinary.")
