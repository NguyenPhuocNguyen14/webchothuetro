from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.db import models
from django.utils import timezone
import re
from urllib.parse import unquote

# helper nhỏ
def _is_url(s: str) -> bool:
    """Simple URL check (http/https)."""
    if not s:
        return False
    s = str(s).strip()
    return bool(re.match(r'^(https?:)?//', s)) or s.startswith('http://') or s.startswith('https://')

def _is_url(val: str) -> bool:
    if not val:
        return False
    s = str(val)
    return s.startswith("http") or "res.cloudinary.com" in s
# ====================
# Khách hàng
# ====================
class Customer(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Tài khoản"
    )
    name = models.CharField("Tên khách hàng", max_length=200, default="Khách hàng")
    email = models.EmailField("Email", max_length=200, null=True, blank=True)
    phone = models.CharField("Số điện thoại", max_length=20, null=True, blank=True)  # ✅ thêm dòng này
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)  # khuyến nghị có luôn

    class Meta:
        verbose_name = "Khách hàng"
        verbose_name_plural = "Danh sách khách hàng"

    def __str__(self):
        return self.name or f"Khách hàng #{self.id}"



# ====================
# Sản phẩm
# ====================
class Product(models.Model):
    CATEGORY_CHOICES = (
        ("shop", "Sản phẩm cửa hàng"),
        ("rental", "Phòng cho thuê"),
    )

    name = models.CharField("Tên sản phẩm", max_length=200, default="Sản phẩm")
    price = models.DecimalField("Giá tiền (VNĐ)", max_digits=12, decimal_places=0, default=0)
    digital = models.BooleanField("Sản phẩm số (Digital)", default=False)
    category = models.CharField("Loại", max_length=20, choices=CATEGORY_CHOICES, default="shop")
    location = models.CharField("Địa chỉ", max_length=300, null=True, blank=True)
    DISTRICT_CHOICES = [
        ("Tân Phú", "Tân Phú"),
        ("Bình Tân", "Bình Tân"),
        ("Tân Bình", "Tân Bình"),
        ("Gò Vấp", "Gò Vấp"),
        ("Quận 1", "Quận 1"),
        ("Quận 3", "Quận 3"),
        ("Phú Nhuận", "Phú Nhuận"),
        ("Bình Thạnh", "Bình Thạnh"),
    ]

    district = models.CharField("Quận", max_length=100, choices=DISTRICT_CHOICES, default="Tân Phú")

    size = models.CharField("Diện tích", max_length=50, null=True, blank=True)
    description = models.TextField("Mô tả", null=True, blank=True)
    image = models.ImageField(upload_to="products/", null=True, blank=True, verbose_name="Ảnh chính")
    views = models.PositiveIntegerField("Lượt xem", default=0)

    # ====== Khuyến mãi ======
    discount_percent = models.PositiveIntegerField("Giảm giá (%)", default=0)

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Danh sách sản phẩm"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.name} - {self.gia_hien_thi}"

    @property
    def gia_giam(self):
        """Trả về giá đã giảm (nếu có), ngược lại giá gốc"""
        if self.discount_percent > 0 and self.price:
            return int(self.price * (100 - self.discount_percent) / 100)
        return int(self.price or 0)

    @property
    def gia_hien_thi(self):
        """Chuẩn hóa format giá hiển thị"""
        if self.discount_percent > 0:
            return f"{self.gia_giam:,.0f} VNĐ (giảm {self.discount_percent}%)"
        return f"{self.price:,.0f} VNĐ" if self.price else "Liên hệ"

    @property
    def image_url(self):
        """
        Trả về URL an toàn cho ảnh chính:
        - Nếu field lưu trực tiếp URL string -> trả thẳng
        - Nếu là FieldFile (ImageField) -> trả image.url (nếu có)
        - Nếu DB lưu dạng encode 'media/https%3A/...' -> decode
        """
        if not self.image:
            return None

        s = str(self.image)

        # fix trường hợp lưu dạng media/https%3A/...
        if "%3A" in s or s.startswith("media/https") or s.startswith("/media/https"):
            s = unquote(s)
            s = s.replace('/media/', '').replace('media/', '')

        # nếu đã là URL -> trả luôn
        if _is_url(s):
            # ensure scheme present (some values may start with //)
            if s.startswith("//"):
                return "https:" + s
            return s

        # else try to use Django storage .url (works for Cloudinary storage or local)
        try:
            return self.image.url
        except Exception:
            return None


    @property
def get_all_images(self):
    """
    Lấy list các URL ảnh (ảnh chính + ảnh phụ) dạng string.
    Bỏ qua link /media/... nếu không tồn tại hoặc không phải URL hợp lệ.
    """
    images = []
    if self.image_url:
        images.append(self.image_url)

    for img in self.images.all():
        u = getattr(img, "image_url", None)
        # chỉ thêm nếu URL thật sự là Cloudinary hoặc link http(s)
        if u and (u.startswith("http") or u.startswith("https")):
            images.append(u)
    return images


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products/", verbose_name="Ảnh phụ")

    @property
    def image_url(self):
        if not self.image:
            return None
        s = str(self.image)
        if "%3A" in s or s.startswith("media/https") or s.startswith("/media/https"):
            s = unquote(s).replace('/media/', '').replace('media/', '')
        if _is_url(s):
            if s.startswith("//"):
                return "https:" + s
            return s
        try:
            return self.image.url
        except Exception:
            return None


# ProductVideo
class ProductVideo(models.Model):
    product = models.ForeignKey(Product, related_name="videos", on_delete=models.CASCADE)
    video = models.FileField(upload_to="products/videos/", verbose_name="Video sản phẩm")

    @property
    def video_url(self):
        if not self.video:
            return None
        s = str(self.video)
        if "%3A" in s or s.startswith("media/https") or s.startswith("/media/https"):
            s = unquote(s).replace('/media/', '').replace('media/', '')
        if _is_url(s):
            if s.startswith("//"):
                return "https:" + s
            return s
        try:
            return self.video.url
        except Exception:
            return None

# ====================
# Đơn hàng
# ====================
class Order(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Khách hàng"
    )
    date_order = models.DateTimeField("Ngày đặt hàng", auto_now_add=True)
    complete = models.BooleanField("Hoàn thành", default=False)
    transaction_id = models.CharField("Mã giao dịch", max_length=200, null=True, blank=True)

    shipping_address = models.ForeignKey(
        "ShippingAddress",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Địa chỉ giao hàng"
    )

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Danh sách đơn hàng"
        ordering = ["-date_order"]

    def __str__(self):
        return f"Đơn hàng #{self.id} ({self.tong_san_pham} SP - {self.tong_tien:,.0f} VNĐ)"

    @property
    def tong_tien(self):
        return sum(item.thanh_tien for item in self.orderitem_set.all())

    @property
    def tong_san_pham(self):
        return self.orderitem_set.aggregate(total=Sum("quantity"))["total"] or 0


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Sản phẩm")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Đơn hàng")
    quantity = models.PositiveIntegerField("Số lượng", default=1)
    date_added = models.DateTimeField("Ngày thêm", auto_now_add=True)

    class Meta:
        verbose_name = "Chi tiết đơn hàng"
        verbose_name_plural = "Danh sách chi tiết đơn hàng"
        constraints = [
            models.UniqueConstraint(fields=["order", "product"], name="unique_order_product")
        ]

    def __str__(self):
        if self.product:
            return f"{self.product.name} ({self.quantity} x {self.product.gia_giam:,.0f}) = {self.thanh_tien:,.0f} VNĐ"
        return f"Sản phẩm x {self.quantity}"

    @property
    def thanh_tien(self):
        if self.product:
            return self.product.gia_giam * self.quantity
        return 0


class ShippingAddress(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Khách hàng"
    )
    address = models.CharField("Địa chỉ", max_length=200)
    city = models.CharField("Thành phố", max_length=200)
    state = models.CharField("Tỉnh / Bang", max_length=200)
    country = models.CharField("Quốc gia", max_length=200, blank=True, null=True)
    mobile = models.CharField("Số điện thoại", max_length=20, blank=True, null=True)
    created_at = models.DateTimeField("Ngày tạo", default=timezone.now)

    class Meta:
        verbose_name = "Địa chỉ giao hàng"
        verbose_name_plural = "Danh sách địa chỉ giao hàng"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.address}, {self.city} ({self.mobile or 'Không có số'})"


# ====================
# Wishlist & Bình luận
# ====================
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Người dùng")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Sản phẩm")
    date_added = models.DateTimeField("Ngày thêm", auto_now_add=True)

    class Meta:
        verbose_name = "Yêu thích"
        verbose_name_plural = "Danh sách yêu thích"
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="unique_user_product")
        ]
        ordering = ["-date_added"]

    def __str__(self):
        return f"{self.user.username} ❤ {self.product.name}"


class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField("Tên người bình luận", max_length=100, blank=True, null=True)  # 🆕 thêm dòng này
    user = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField("Nội dung bình luận")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bình luận"
        verbose_name_plural = "Danh sách bình luận"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.name if self.user else 'Khách'} - {self.product.name}"



# ====================
# Chat AI (Gemini)
# ====================
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField("Tin nhắn")
    response = models.TextField("Phản hồi AI", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat AI"
        verbose_name_plural = "Lịch sử chat AI"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.message[:30]}"


# ====================
# Chat trực tiếp User ↔ Admin
# ====================
class DirectChatMessage(models.Model):
    SENDER_CHOICES = (
        ("user", "Người dùng"),
        ("admin", "Admin"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="direct_chats")
    sender = models.CharField("Người gửi", max_length=10, choices=SENDER_CHOICES)
    message = models.TextField("Nội dung tin nhắn", blank=True, null=True)
    image = models.ImageField("Ảnh", upload_to="chat_images/", blank=True, null=True)
    is_read = models.BooleanField("Đã đọc", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tin nhắn trực tiếp"
        verbose_name_plural = "Hộp thoại trực tiếp"
        ordering = ["created_at"]

    def __str__(self):
        if self.message:
            return f"{self.user.username} - {self.sender}: {self.message[:20]}"
        return f"{self.user.username} - {self.sender}: 📷 Hình ảnh"


# ====================
# Video
# ====================
class Video(models.Model):
    title = models.CharField("Tiêu đề", max_length=200)
    description = models.TextField("Mô tả", blank=True, null=True)
    file = models.FileField("Video", upload_to="videos/", blank=True, null=True)
    url = models.URLField("Link video ngoài", blank=True, null=True)
    thumbnail = models.ImageField("Ảnh đại diện", upload_to="videos/thumbnails/", blank=True, null=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Danh sách video"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def get_source(self):
        """Trả về link video (ưu tiên file upload, fallback sang url ngoài)"""
        if self.file:
            return self.file.url
        return self.url or ""
    
    
class Contact(models.Model):
    name = models.CharField(max_length=200, verbose_name="Họ và tên")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Số điện thoại")
    message = models.TextField(verbose_name="Nội dung")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Liên hệ"
        verbose_name_plural = "Danh sách liên hệ"

    def __str__(self):
        return f"{self.name} - {self.email}"

