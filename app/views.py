# app/views.py
import json
import re
import os
from typing import Tuple
from .models import Video 
from django.core.mail import send_mail
from django.conf import settings 
from django.urls import reverse
from .models import Contact
from .forms import SignupForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from dotenv import load_dotenv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import ShippingAddress, Order

from django.db import transaction
from django.db.models import F, Q, Sum, FloatField, Count
from django.db.models.functions import Coalesce  # ✅ thêm để tránh NULL

from .models import (
    Product, Order, OrderItem, Wishlist,
    Customer, Comment, ChatMessage, DirectChatMessage
)
from .services import ask_with_products
from .utils import ask_gemini
# =====================
# Config
# =====================
load_dotenv()


# =====================
# Chatbot
# =====================
@csrf_exempt
def chatbot_reply(request):
    """Chatbot có tìm sản phẩm trong DB"""
    user_msg = request.GET.get("msg") or request.POST.get("msg", "")
    reply = ask_with_products(user_msg)
    return JsonResponse({"reply": reply})


@csrf_exempt
def chatbot_ai(request):
    """Chatbot AI (kết hợp dữ liệu sản phẩm)"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_msg = data.get("message", "").strip()

            if not user_msg:
                return JsonResponse({"answer": "Bạn chưa nhập câu hỏi 😅"})

            # Dùng hàm có tìm sản phẩm trong DB
            answer = ask_with_products(user_msg)

            # Lưu vào DB (chỉ khi model cho phép null user)
            ChatMessage.objects.create(
                user=request.user if request.user.is_authenticated else None,
                message=user_msg,
                response=answer,
            )
            return JsonResponse({"answer": answer})

        except Exception as e:
            return JsonResponse({"answer": f"🚨 Đã xảy ra lỗi: {str(e)}"})
    return JsonResponse({"answer": "Phương thức không hợp lệ"}, status=400)


# =====================
# Helper để đảm bảo user luôn có Customer
# =====================
def get_or_create_customer(user):
    """Đảm bảo user luôn có Customer liên kết"""
    if not hasattr(user, "customer"):
        customer, _ = Customer.objects.get_or_create(
            user=user,
            defaults={
                "name": user.username,
                "email": user.email,
            },
        )
        return customer
    return user.customer


# =====================
# Helper / Utils
# =====================
def get_cart_info(user) -> Tuple[int, float]:
    """Trả về tổng số lượng và tổng tiền (ưu tiên giá giảm)."""
    if user.is_authenticated and hasattr(user, "customer"):
        customer = user.customer
        order = (
            Order.objects.filter(customer=customer, complete=False)
            .prefetch_related("orderitem_set__product")
            .first()
        )
        if order:
            total_quantity = 0
            total_price = 0
            for item in order.orderitem_set.all():
                if not item.product:
                    continue
                total_quantity += item.quantity
                total_price += item.product.gia_giam * item.quantity
            return total_quantity, float(total_price)
    return 0, 0



def get_wishlist_count(user) -> int:
    if user.is_authenticated:
        return Wishlist.objects.filter(user=user).count()
    return 0


def extract_district_from_location(location: str) -> str:
    if not location:
        return None
    parts = re.split(r"[-,\/\|]", location)
    for part in reversed(parts):
        name = part.strip()
        if name and name.lower() not in ["không có địa chỉ", "unknown"]:
            return name
    return location.strip()


def get_base_context(request) -> dict:
    incomplete_count, incomplete_total = get_cart_info(request.user)
    wishlist_count = get_wishlist_count(request.user)
    return {
        "incomplete_count": incomplete_count,
        "incomplete_total": incomplete_total,
        "wishlist_count": wishlist_count,
    }


# =====================
# Trang chủ
# =====================
def home(request):
    products = Product.objects.order_by("-id")[:12]
    popular_products = Product.objects.annotate(
        wish_count=Count("wishlist")
    ).order_by("-wish_count", "-id")[:8]
    sale_products = Product.objects.filter(discount_percent__gt=0).order_by("-id")[:8]
    video = Video.objects.order_by("-created_at").first()  # ✅ chỉ lấy 1 video mới nhất

    context = get_base_context(request)
    context.update({
        "products": products,
        "popular_products": popular_products,
        "sale_products": sale_products,
        "video": video,  # ✅ truyền 1 video duy nhất
    })
    return render(request, "app/home.html", context)



# =====================
# Trang sản phẩm
# =====================
def product_page(request):
    qs = Product.objects.all()

    # --- Params ---
    query       = (request.GET.get("q") or "").strip()
    district    = request.GET.get("district") or ""
    category    = request.GET.get("category") or ""
    price_range = request.GET.get("price_range") or ""
    sort        = request.GET.get("sort") or ""

    # --- Keyword search (name + location) ---
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(location__icontains=query))

    # --- Price range ---
    if price_range == "under2":
        qs = qs.filter(price__lt=2_000_000)
    elif price_range == "2to4":
        qs = qs.filter(price__gte=2_000_000, price__lt=4_000_000)
    elif price_range == "4to6":
        qs = qs.filter(price__gte=4_000_000, price__lt=6_000_000)
    elif price_range == "over6":
        qs = qs.filter(price__gte=6_000_000)

    # --- District filter ---
    if district:
        # Nếu có field "district" (và DB đã migrate), dùng đúng field; nếu không, fallback location__icontains
        try:
            # Thử build queryset dùng field district; nếu field không tồn tại -> FieldError
            Product._meta.get_field("district")  # chỉ kiểm tra metadata
            qs = qs.filter(district=district)
        except Exception:
            # Fallback theo location chứa tên quận
            qs = qs.filter(location__icontains=district)

    # --- Category filter ---
    if category:
        # vì category là ChoiceField -> filter chính xác theo value (shop / rental)
        qs = qs.filter(category=category)

    # --- Sort ---
    if sort == "price_asc":
        qs = qs.order_by("price")
    elif sort == "price_desc":
        qs = qs.order_by("-price")
    else:
        qs = qs.order_by("-id")

    # --- Pagination ---
    paginator = Paginator(qs, 12)
    page = request.GET.get("page")
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # --- Build dynamic filter lists ---
    # Categories: lấy từ choices trong model
    categories = Product.CATEGORY_CHOICES

    # Price ranges: nhãn hiển thị
    price_ranges = [
        ("under2", "Dưới 2 triệu"),
        ("2to4", "2–4 triệu"),
        ("4to6", "4–6 triệu"),
        ("over6", "Trên 6 triệu"),
    ]

    # Districts:
    # 1) Nếu model có field district (và bạn đã migrate), hiển thị theo DISTRICT_CHOICES (nhãn bên phải)
    # 2) Nếu không có, sinh từ location (distinct) và rút trích quận bằng hàm extract_district_from_location đã có.
    try:
        Product._meta.get_field("district")
        districts = [label for _, label in getattr(Product, "DISTRICT_CHOICES", [])] or []
    except Exception:
        raw_locations = (
            Product.objects.exclude(location__isnull=True)
            .exclude(location__exact="")
            .values_list("location", flat=True)
            .distinct()
        )
        # dùng helper extract_district_from_location đã có trong views
        tmp = {}
        for loc in raw_locations:
            d = extract_district_from_location(loc)
            if d:
                tmp[d] = True
        districts = sorted(tmp.keys())

    # --- Context ---
    context = get_base_context(request)
    context.update({
        "products": products,
        "page_obj": products,
        "is_paginated": products.has_other_pages(),
        "categories": categories,
        "price_ranges": price_ranges,
        "districts": districts,

        # Current selections
        "search_query": query,
        "current_district": district,
        "current_category": category,
        "current_price_range": price_range,
        "current_sort": sort,
    })
    return render(request, "app/product.html", context)

# =====================
# Chi tiết sản phẩm
# =====================
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Product.objects.filter(pk=product.pk).update(views=F("views") + 1)
    product.refresh_from_db()
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:8]

    context = get_base_context(request)
    context.update({
        "product": product,
        "products": related_products,
    })
    return render(request, "app/product_detail.html", context)


# =====================
# Giỏ hàng (có thêm lịch sử mua hàng)
# =====================
@login_required
def cart_view(request):
    customer = get_or_create_customer(request.user)
    order = Order.objects.filter(customer=customer, complete=False).first()
    if not order:
        order = Order.objects.create(customer=customer, complete=False)

    items = order.orderitem_set.select_related("product")

    cart_products = []
    for item in items:
        if not item.product:
            item.delete()
            continue
        unit_price = item.product.gia_giam
        cart_products.append({
            "product": item.product,
            "unit_price": unit_price,
            "total_quantity": item.quantity,
            "total_price": unit_price * item.quantity,
            "order_ids": [order.id],
        })

    # ✅ Lấy danh sách đơn hàng đã hoàn tất (lịch sử mua hàng)
    past_orders = (
        Order.objects.filter(customer=customer, complete=True)
        .prefetch_related("orderitem_set__product")
        .order_by("-date_order")   # 🔥 sửa lại ở đây
    )

    context = get_base_context(request)
    context.update({
        "cart_products": cart_products,
        "incomplete_items": items,
        "past_orders": past_orders,
    })
    return render(request, "app/cart.html", context)


# =====================
# Lịch sử mua hàng (trang riêng)
# =====================
@login_required
def order_history(request):
    customer = get_or_create_customer(request.user)
    orders = (
        Order.objects.filter(customer=customer, complete=True)
        .prefetch_related("orderitem_set__product")
        .order_by("-date_order")   # 🔥 sửa lại ở đây
    )

    context = get_base_context(request)
    context["orders"] = orders
    return render(request, "app/order_history.html", context)



# =====================
# API Update Cart
# =====================
from django.contrib.auth.decorators import login_required

# Helper đảm bảo luôn có Customer
def get_or_create_customer(user):
    if not hasattr(user, "customer"):
        customer, _ = Customer.objects.get_or_create(
            user=user,
            defaults={
                "name": user.username,
                "email": user.email,
            },
        )
        return customer
    return user.customer


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.shortcuts import get_object_or_404

@require_POST
def update_item(request):
    """
    API cập nhật giỏ hàng (POST JSON):
    - Trả 401 nếu user chưa authenticate (frontend sẽ redirect về login)
    - Trả JSON mô tả tổng số lượng + tổng giá
    """
    # nếu chưa login -> trả 401 (frontend redirect)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "not_authenticated"}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    product_id = data.get("productId")
    action = data.get("action")

    if not product_id or not action:
        return JsonResponse({"error": "Missing productId or action"}, status=400)

    product = get_object_or_404(Product, id=product_id)
    customer = get_or_create_customer(request.user)
    order, _ = Order.objects.get_or_create(customer=customer, complete=False)

    with transaction.atomic():
        order_item, created = OrderItem.objects.select_for_update().get_or_create(
            order=order, product=product, defaults={"quantity": 0}
        )

        if action == "add":
            order_item.quantity += 1
        elif action == "remove":
            order_item.quantity -= 1
        elif action == "delete":
            order_item.delete()
            total_quantity = sum(i.quantity for i in order.orderitem_set.all())
            total_price = sum(i.thanh_tien for i in order.orderitem_set.all())
            return JsonResponse({
                "status": "deleted",
                "product_id": product.id,
                "total_quantity": total_quantity,
                "total_price": total_price,
            })
        else:
            return JsonResponse({"error": "Unknown action"}, status=400)

        if order_item.quantity <= 0:
            order_item.delete()
        else:
            order_item.save()

    total_quantity = sum(i.quantity for i in order.orderitem_set.all())
    total_price = sum(i.thanh_tien for i in order.orderitem_set.all())

    return JsonResponse({
        "status": "ok",
        "product_id": product.id,
        "quantity": getattr(order_item, "quantity", 0),
        "item_total": getattr(order_item, "thanh_tien", 0),
        "total_quantity": total_quantity,
        "total_price": total_price,
    })



# =====================
# Checkout
# =====================
@login_required
def checkout_view(request):
    customer = get_or_create_customer(request.user)
    order = Order.objects.filter(customer=customer, complete=False).first()
    if not order:
        order = Order.objects.create(customer=customer, complete=False)

    items = order.orderitem_set.select_related("product")

    cart_products = []
    for item in items:
        if not item.product:
            item.delete()
            continue
        unit_price = item.product.gia_giam
        cart_products.append({
            "product": item.product,
            "total_quantity": item.quantity,
            "total_price": unit_price * item.quantity,
            "unit_price": unit_price,
        })

    context = get_base_context(request)
    context.update({
        "cart_products": cart_products,
        "incomplete_items": items,
    })
    return render(request, "app/checkout.html", context)

# =====================
# Wishlist
# =====================
@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related("product")
    context = get_base_context(request)
    context["wishlist_items"] = items
    return render(request, "app/wishlist.html", context)





# =====================
# API Toggle Wishlist
# =====================
@require_POST
@login_required
def toggle_wishlist(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    product_id = data.get("product_id")
    if not product_id:
        return JsonResponse({"error": "Missing product_id"}, status=400)

    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    status = "added" if created else "removed"
    if not created:
        wishlist_item.delete()

    current_wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse({
        "status": status,
        "product_id": product.id,
        "wishlist_count": current_wishlist_count,
    })


# =====================
# Authentication
# =====================
def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Tạo Customer nếu chưa có
            Customer.objects.get_or_create(
                user=user,
                defaults={
                    "name": user.username,
                    "email": user.email,
                    "phone": getattr(user, "phone", None)
                }
            )
            login(request, user)
            messages.success(request, "🎉 Đăng ký thành công! Chào mừng bạn.")
            return redirect("home")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"⚠️ Lỗi ở trường '{field}': {error}")
    else:
        form = SignupForm()
    return render(request, "app/signup.html", {"form": form})



def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "✅ Đăng nhập thành công!")
            return redirect("home")
        else:
            messages.error(request, "❌ Sai thông tin đăng nhập!")
    else:
        form = AuthenticationForm()
    return render(request, "app/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "👋 Bạn đã đăng xuất thành công!")
    return redirect("home")


# =====================
# API Comment
# =====================
@csrf_exempt
def add_comment(request, product_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Phương thức không hợp lệ"})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON không hợp lệ"})

    content = data.get("content", "").strip()
    if not content:
        return JsonResponse({"success": False, "error": "Nội dung trống"})

    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated and hasattr(request.user, "customer"):
        customer = request.user.customer
        # ✅ Dùng fallback nếu Customer chưa có tên
        name = customer.name.strip() if customer.name else request.user.username
    else:
        customer = None
        name = "Khách"

    comment = Comment.objects.create(
        product=product,
        user=customer,
        name=name,
        content=content
    )

    return JsonResponse({
        "success": True,
        "user": name,  # ✅ gửi về đúng tên người bình luận
        "content": comment.content,
        "created_at": comment.created_at.strftime("%H:%M %d/%m/%Y")
    })




def tu_van(request):
    return render(request, "app/tu_van.html")
# =====================
# Chat trực tiếp User ↔ Admin
# =====================
from django.contrib.auth.models import User

@login_required
def direct_chat_user(request):
    """User xem & gửi tin nhắn với admin"""
    chat_messages = DirectChatMessage.objects.filter(user=request.user).order_by("created_at")
    return render(request, "app/direct_chat_user.html", {"messages": chat_messages})


@login_required
def direct_chat_admin(request):
    """Admin dashboard: xem danh sách user để chat"""
    if not request.user.is_staff:
        return redirect("home")

    users = User.objects.all().exclude(is_staff=True)
    return render(request, "app/direct_chat_admin.html", {"users": users})

@login_required
@require_POST
def send_direct_message(request):
    msg = (request.POST.get("message") or "").strip()

    img = request.FILES.get("image")

    from django.contrib.auth import get_user_model
    User = get_user_model()

    if request.user.is_staff:
        # 👨‍💻 Admin gửi → cần user_id để biết gửi cho ai
        user_id = request.POST.get("user_id")
        if not user_id:
            return JsonResponse({"error": "Thiếu user_id"}, status=400)
        target_user = get_object_or_404(User, id=user_id)

        if msg or img:
            DirectChatMessage.objects.create(
                user=target_user,
                sender="admin",
                message=msg or "",
                image=img if img else None
            )
        return redirect(f"/admin/app/directchatmessage/{target_user.id}/")

    else:
        # 👤 User gửi → chỉ cần gắn user hiện tại
        if msg or img:
            DirectChatMessage.objects.create(
                user=request.user,
                sender="user",
                message=msg or "",
                image=img if img else None
            )
        return JsonResponse({"success": True})


    
@login_required
def get_direct_messages(request, user_id=None):
    """API lấy tin nhắn"""
    if request.user.is_staff:
        if not user_id:
            return JsonResponse([], safe=False)
        target_user = get_object_or_404(User, id=user_id)
        messages = DirectChatMessage.objects.filter(user=target_user).order_by("created_at")
    else:
        messages = DirectChatMessage.objects.filter(user=request.user).order_by("created_at")

    data = []
    for m in messages:
        data.append({
            "sender": m.sender,
            "message": m.message or "",
            "image": m.image.url if m.image else None,  # ✅ gửi url ảnh về frontend
            "created_at": m.created_at.isoformat(),    # gửi chuẩn ISO -> JS parse được
        })
    return JsonResponse(data, safe=False)
# =====================
# Danh sách video
# =====================
def video_list(request):
    """Trang hiển thị danh sách video"""
    videos = Video.objects.all().order_by("-created_at")
    context = get_base_context(request)
    context["videos"] = videos
    return render(request, "app/video_list.html", context)
# =====================
# Chi tiết video
# =====================
def video_detail(request, video_id):
    """Trang chi tiết video"""
    video = get_object_or_404(Video, id=video_id)
    context = get_base_context(request)
    context["video"] = video
    return render(request, "app/video_detail.html", context)

# =====================
# Process Order
# =====================
@login_required
def process_order(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        mobile = request.POST.get("mobile")
        country = request.POST.get("country")
        payment = request.POST.get("payment", "COD")

        # ✅ Đảm bảo user luôn có Customer
        customer = get_or_create_customer(request.user)

        # Lấy order chưa hoàn thành
        order = Order.objects.filter(customer=customer, complete=False).first()
        if not order:
            order = Order.objects.create(customer=customer, complete=False)

        # Nếu giỏ hàng trống thì quay lại cart
        if not order.orderitem_set.exists():
            return redirect("cart")

        # Tạo địa chỉ giao hàng
        shipping = ShippingAddress.objects.create(
            customer=customer,
            address=address,
            city=city,
            state=state,
            mobile=mobile,
            country=country,
        )

        # Hoàn tất đơn hàng
        order.complete = True
        order.shipping_address = shipping
        order.save()

        return redirect("order_success", order_id=order.id)

    return redirect("checkout_view")

@login_required
def order_success(request, order_id):
    # ✅ dùng get_or_create_customer thay vì request.user.customer
    customer = get_or_create_customer(request.user)
    order = get_object_or_404(Order, id=order_id, customer=customer)
    return render(request, "app/order_success.html", {"order": order})


def contact_view(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        message = (request.POST.get("message") or "").strip()

        if name and email and message:
            # ✅ Lưu DB
            Contact.objects.create(
                name=name, email=email, phone=phone, message=message
            )

            # ✅ Gửi mail cho admin
            subject = f"📩 Liên hệ từ {name}"
            body = (
                f"Người gửi: {name}\n"
                f"Email: {email}\n"
                f"Số điện thoại: {phone or 'Không cung cấp'}\n\n"
                f"Nội dung:\n{message}"
            )
            try:
                send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACT_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, "✅ Gửi liên hệ thành công! Chúng tôi sẽ phản hồi sớm.")
            except Exception as e:
                messages.error(request, f"❌ Lỗi khi gửi mail: {e}")
        else:
            messages.error(request, "⚠️ Vui lòng điền đầy đủ thông tin.")

    return render(request, "app/contact.html")

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)
    return render(request, "app/order_detail.html", {"order": order})

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

@login_required
def delete_order(request, order_id):
    """Xóa đơn hàng đã hoàn tất (chỉ của user hiện tại)"""
    order = get_object_or_404(Order, id=order_id, customer=request.user.customer)

    if request.method == "POST":
        if order.complete:  # chỉ cho xoá đơn đã hoàn tất
            order.delete()
            messages.success(request, f"🗑 Đã xoá đơn hàng #{order_id}")
        else:
            messages.warning(request, "⚠ Không thể xoá đơn chưa hoàn tất!")
        return redirect("order_history")
    
    return redirect("order_history")


def product_view(request):
    products = Product.objects.all()

    # ====== Lọc theo từ khóa ======
    q = request.GET.get('q', '').strip()
    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(location__icontains=q) |
            Q(description__icontains=q)
        )

    # ====== Lọc theo khoảng giá ======
    price_range = request.GET.get('price_range')
    if price_range == 'under2':
        products = products.filter(price__lt=2000000)
    elif price_range == '2to4':
        products = products.filter(price__gte=2000000, price__lt=4000000)
    elif price_range == '4to6':
        products = products.filter(price__gte=4000000, price__lt=6000000)
    elif price_range == 'over6':
        products = products.filter(price__gte=6000000)

    # ====== Lọc theo quận ======
    district = request.GET.get('district')
    if district:
        products = products.filter(location__icontains=district)

    # ====== Lọc theo loại ======
    category = request.GET.get('category')
    if category:
        products = products.filter(category__iexact=category)

    # ====== Chuẩn bị dữ liệu bộ lọc (tự động từ DB) ======
    districts = (
        Product.objects.exclude(location__isnull=True)
        .exclude(location__exact="")
        .values_list("location", flat=True)
        .distinct()
        .order_by("location")
    )

    categories = Product.CATEGORY_CHOICES  # Nếu bạn dùng tuple trong model

    # ====== Trả về template ======
    context = {
        "products": products,
        "districts": districts,
        "categories": categories,
    }
    return render(request, "app/product.html", context)