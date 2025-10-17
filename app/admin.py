from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render
from django.db.models import Max, Count, Q, OuterRef, Subquery
from .models import Contact

from .models import (
    Customer, Product, ProductImage, ProductVideo, Order, OrderItem,
    ShippingAddress, Wishlist, Comment, DirectChatMessage, Video
)

# ====================
# Helper format
# ====================
def format_vnd(value):
    try:
        return "{:,.0f} VNĐ".format(value).replace(",", ".")
    except Exception:
        return "0 VNĐ"


# ====================
# Product form
# ====================
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if isinstance(price, str):
            price = price.replace(".", "").replace(",", "")
        return price


# ====================
# Customer Admin
# ====================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "phone", "user", "created_at")
    search_fields = ("name", "email", "phone")
    list_filter = ("created_at",)
    list_per_page = 20

    @admin.display(description="Tên khách hàng")
    def ten_khach_hang(self, obj):
        return obj.name

    @admin.display(description="Email")
    def email_display(self, obj):
        return obj.email or "—"

    @admin.display(description="Số điện thoại")
    def phone_display(self, obj):
        return obj.phone or "—"




# ====================
# ProductImage Inline
# ====================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "preview")
    readonly_fields = ("preview",)

    @admin.display(description="Xem trước")
    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:80px;border-radius:6px;" />', obj.image.url)
        return "—"


# ====================
# ProductVideo Inline
# ====================
class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1
    fields = ("video", "preview")
    readonly_fields = ("preview",)

    @admin.display(description="Xem trước")
    def preview(self, obj):
        if obj.video:
            return format_html(
                """
                <video width="160" height="90" controls>
                    <source src="{}" type="video/mp4">
                </video>
                """,
                obj.video.url,
            )
        return "—"


# ====================
# Product Admin
# ====================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = (
        "id",
        "ten_san_pham",
        "gia_tien",
        "loai",
        "quan",
        "dia_chi",
        "dien_tich",
        "san_pham_so",
        "anh_chinh",
    )
    list_filter = ("category", "district", "digital")
    search_fields = ("name", "location")
    inlines = [ProductImageInline, ProductVideoInline]
    list_per_page = 20

    fieldsets = (
        ("Thông tin cơ bản", {
            "fields": (
                "name",
                "price",
                "discount_percent",
                "digital",
                "category",
                "district",
                "description",
                "image"
            )
        }),
        ("Thông tin bổ sung (phòng trọ)", {
            "fields": ("location", "size"),
            "classes": ("collapse",)
        }),
    )

    @admin.display(description="Tên sản phẩm")
    def ten_san_pham(self, obj):
        return obj.name

    @admin.display(description="Giá tiền")
    def gia_tien(self, obj):
        if obj.discount_percent > 0:
            return format_html(
                '<span style="text-decoration:line-through;color:#999;">{}</span> → '
                '<span style="color:#e63946;">{}</span>',
                format_vnd(obj.price),
                format_vnd(obj.gia_giam),
            )
        return format_vnd(obj.price)

    @admin.display(description="Loại")
    def loai(self, obj):
        return obj.get_category_display()

    @admin.display(description="Quận")
    def quan(self, obj):
        return obj.get_district_display() if obj.district else "—"

    @admin.display(description="Địa chỉ")
    def dia_chi(self, obj):
        return obj.location or "—"

    @admin.display(description="Diện tích")
    def dien_tich(self, obj):
        return obj.size or "—"

    @admin.display(description="Sản phẩm số")
    def san_pham_so(self, obj):
        return "Có" if obj.digital else "Không"

    @admin.display(description="Ảnh chính")
    def anh_chinh(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px;" />', obj.image.url)
        return "—"



# ====================
# OrderItem Inline
# ====================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "quantity", "thanh_tien", "preview")
    readonly_fields = ("thanh_tien", "preview")

    @admin.display(description="Thành tiền")
    def thanh_tien(self, obj):
        if obj.product:
            return format_vnd(obj.thanh_tien)
        return "0 VNĐ"

    @admin.display(description="Ảnh")
    def preview(self, obj):
        if obj.product and obj.product.image:
            return format_html('<img src="{}" style="height:50px;border-radius:4px;" />', obj.product.image.url)
        return "—"


# ====================
# Order Admin
# ====================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "date_order", "hoan_thanh", "transaction_id", "tong_tien")
    list_filter = ("complete", "date_order")
    search_fields = ("transaction_id",)
    inlines = [OrderItemInline]
    list_per_page = 20

    @admin.display(description="Hoàn thành")
    def hoan_thanh(self, obj):
        return "✔️" if obj.complete else "❌"

    @admin.display(description="Tổng tiền")
    def tong_tien(self, obj):
        return format_vnd(obj.tong_tien)


# ====================
# OrderItem Admin
# ====================
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "order", "quantity", "thanh_tien", "date_added")
    list_filter = ("date_added",)
    search_fields = ("product__name",)
    list_per_page = 20

    @admin.display(description="Thành tiền")
    def thanh_tien(self, obj):
        if obj.product:
            return format_vnd(obj.thanh_tien)
        return "0 VNĐ"


# ====================
# ShippingAddress Admin
# ====================
@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "dia_chi_day_du",
        "san_pham_da_dat",
        "tong_tien_don_hang",
        "created_at",
    )
    search_fields = ("address", "city", "state", "country", "mobile")
    list_filter = ("city", "state", "country", "created_at")

    @admin.display(description="Địa chỉ đầy đủ")
    def dia_chi_day_du(self, obj):
        return f"{obj.address}, {obj.city}, {obj.state}, {obj.country}"

    @admin.display(description="Sản phẩm đã đặt")
    def san_pham_da_dat(self, obj):
        order = obj.orders.first()
        if not order:
            return "—"
        items = order.orderitem_set.all()
        return format_html("<br>".join([
            f"{item.product.name} x {item.quantity} → <b>{format_vnd(item.thanh_tien)}</b>"
            for item in items
        ])) if items else "—"

    @admin.display(description="Tổng tiền đơn hàng")
    def tong_tien_don_hang(self, obj):
        order = obj.orders.first()
        if not order:
            return "0 VNĐ"
        return format_vnd(order.tong_tien)


# ====================
# Wishlist Admin
# ====================
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "date_added")
    search_fields = ("user__username", "product__name")
    list_filter = ("date_added",)
    list_per_page = 20


# ====================
# Comment Admin
# ====================
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "user", "short_content", "created_at")
    search_fields = ("product__name", "user__name", "content")
    list_filter = ("created_at",)
    list_per_page = 30

    @admin.display(description="Nội dung")
    def short_content(self, obj):
        return obj.content[:50] + ("..." if len(obj.content) > 50 else "")


# ====================
# DirectChatMessage Admin
# ====================
@admin.register(DirectChatMessage)
class DirectChatMessageAdmin(admin.ModelAdmin):
    list_display = ("user_link", "last_message", "unread_count", "total_messages", "last_time")
    search_fields = ("user__username",)

    @admin.display(description="Người dùng")
    def user_link(self, obj):
        url = reverse("admin:directchatmessage_detail", args=[obj.user.id])
        return format_html('<a href="{}">💬 {}</a>', url, obj.user.username)

    @admin.display(description="Tin nhắn gần nhất")
    def last_message(self, obj):
        return obj.last_message or "—"

    @admin.display(description="Chưa đọc")
    def unread_count(self, obj):
        return obj.unread_count

    @admin.display(description="Tổng tin nhắn")
    def total_messages(self, obj):
        return obj.total_messages

    @admin.display(description="Thời gian cuối")
    def last_time(self, obj):
        return obj.last_time.strftime("%H:%M %d/%m/%Y") if obj.last_time else "—"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        last_message_subquery = DirectChatMessage.objects.filter(
            user=OuterRef("user")
        ).order_by("-created_at").values("message")[:1]

        return qs.annotate(
            last_time=Max("created_at"),
            total_messages=Count("id"),
            unread_count=Count("id", filter=Q(is_read=False)),
            last_message=Subquery(last_message_subquery),
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:user_id>/",
                self.admin_site.admin_view(self.chat_detail_view),
                name="directchatmessage_detail",
            ),
        ]
        return custom_urls + urls

    def chat_detail_view(self, request, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)

        if request.method == "POST":
            msg = request.POST.get("message", "").strip()
            img = request.FILES.get("image")
            if msg or img:
                DirectChatMessage.objects.create(
                    user=user,
                    sender="admin",
                    message=msg or "",
                    image=img if img else None
                )

        messages = DirectChatMessage.objects.filter(user=user).order_by("created_at")
        return render(request, "admin/direct_chat_admin.html", {
            "messages": messages,
            "user_chat": user,
        })


# ====================
# Video Admin
# ====================
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "short_description", "thumbnail_preview", "video_preview", "created_at")
    search_fields = ("title", "description")
    list_filter = ("created_at",)
    readonly_fields = ("thumbnail_preview", "video_preview", "created_at")
    list_per_page = 20
    ordering = ["-created_at"]

    fieldsets = (
        ("Thông tin cơ bản", {
            "fields": ("title", "description", "created_at")
        }),
        ("Nguồn Video", {
            "fields": ("file", "url", "video_preview")
        }),
        ("Ảnh Thumbnail", {
            "fields": ("thumbnail", "thumbnail_preview")
        }),
    )

    @admin.display(description="Mô tả")
    def short_description(self, obj):
        return (obj.description[:50] + "...") if obj.description and len(obj.description) > 50 else obj.description or "—"

    @admin.display(description="Thumbnail")
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="height:80px;border-radius:6px;" />', obj.thumbnail.url)
        return "—"

    @admin.display(description="Xem trước Video")
    def video_preview(self, obj):
        if obj.file:
            return format_html(
                """
                <video width="220" height="140" controls style="border-radius:6px;">
                    <source src="{}" type="video/mp4">
                </video>
                """, obj.file.url
            )
        if obj.url:
            return format_html(
                """
                <iframe width="220" height="140" src="{}" frameborder="0" allowfullscreen style="border-radius:6px;"></iframe>
                """, obj.url
            )
        return "—"


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "phone", "short_message", "created_at")
    search_fields = ("name", "email", "phone", "message")
    list_filter = ("created_at",)
    list_per_page = 20
    ordering = ["-created_at"]

    @admin.display(description="Nội dung")
    def short_message(self, obj):
        return obj.message[:50] + ("..." if len(obj.message) > 50 else "")

