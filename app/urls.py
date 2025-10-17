from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView

# -------------------
# Custom LogoutView cho phép GET
# -------------------
class MyLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        """Cho phép logout qua GET request"""
        return self.post(request, *args, **kwargs)

# -------------------
# URL Patterns
# -------------------
urlpatterns = [
    # Trang chủ
    path("", views.home, name="home"),

    # Trang sản phẩm

    path("product/", views.product_page, name="product"),
    path("product/<int:product_id>/", views.product_detail, name="product_detail"),
    path("product/<int:product_id>/comment/", views.add_comment, name="add_comment"),

    # Giỏ hàng & Checkout
    path("cart/", views.cart_view, name="cart"),
    path("checkout/", views.checkout_view, name="checkout"),

    # API cập nhật giỏ hàng (AJAX)
    path("update_item/", views.update_item, name="update_item"),

    # Wishlist
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("wishlist/toggle/", views.toggle_wishlist, name="toggle_wishlist"),

    # Đăng nhập
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="app/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),

    # Đăng ký
    path("signup/", views.signup_view, name="signup"),

    # Đăng xuất (cho GET và POST)
    path("logout/", MyLogoutView.as_view(next_page="/"), name="logout"),

    # Chatbot AI
    path("chatbot/", views.chatbot_ai, name="chatbot_ai"),

   # Chat trực tiếp User ↔ Admin
path("direct-chat/", views.direct_chat_user, name="direct_chat"),   # user chat
path("direct-chat-admin/", views.direct_chat_admin, name="direct_chat_admin"),  # admin chat
path("chat/send/", views.send_direct_message, name="send_direct_message"),
path("chat/get/", views.get_direct_messages, name="get_direct_messages"),
path("order/success/<int:order_id>/", views.order_success, name="order_success"),
path("contact/", views.contact_view, name="contact"),
  path("videos/", views.video_list, name="video_list"),
    path("videos/<int:video_id>/", views.video_detail, name="video_detail"),
     path("process_order/", views.process_order, name="process_order"), 
     path("orders/<int:order_id>/", views.order_detail, name="order_detail"), 
     path("orders/history/", views.order_history, name="order_history"),
     path("orders/delete/<int:order_id>/", views.delete_order, name="delete_order"),
    # Django admin
    path("admin/", admin.site.urls),
]
