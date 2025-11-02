# services.py
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import url_has_allowed_host_and_scheme
from .models import Product, Wishlist, Comment
from .utils import ask_gemini


def search_products(query):
    return Product.objects.filter(name__icontains=query)[:5]


def ask_with_products(user_msg, request=None):  # ⚡ nhận thêm request
    products = search_products(user_msg)

    if products.exists():
        product_info = []
        for p in products:
            wishlist_count = Wishlist.objects.filter(product=p).count()
            comment_count = Comment.objects.filter(product=p).count()
            first_image = p.image.url if p.image else ""

            # ✅ link tuyệt đối
            relative_link = reverse("product_detail", args=[p.id])
            if request:
                product_link = request.build_absolute_uri(relative_link)
            else:
                product_link = relative_link  # fallback

            # 👉 Card thông tin
            info = f"""
            <div style='border:1px solid #ddd;padding:10px;border-radius:10px;
                        margin-bottom:15px;background:#fafafa;max-width:270px;'>
                <a href='{product_link}' target='_blank' 
                   style='font-weight:bold;font-size:15px;color:#218c57;text-decoration:none;'>
                   {p.name}
                </a>
                <div style='margin-top:5px;font-size:14px;color:#444;'>
                    💵 {p.price:,} VND<br>
                    📍 {p.location or 'Không có địa chỉ'}<br>
                    ❤️ {wishlist_count} lượt thích | 💬 {comment_count} bình luận
                </div>
            """

            # 👉 Ảnh + link ngay bên dưới
            if first_image:
                info += f"""
                <div style='margin-top:8px;text-align:center;'>
                    <a href='{product_link}' target='_blank'>
                        <img src='{first_image}' alt='{p.name}'
                             style='max-width:100%;border-radius:8px;display:block;margin:0 auto;'/>
                    </a>
                    <a href='{product_link}' target='_blank' 
                       style='display:inline-block;margin-top:6px;color:#218c57;font-weight:bold;'>
                       🔗 Xem chi tiết
                    </a>
                </div>
                """
            else:
                info += f"""
                <div style='margin-top:8px;'>
                    <a href='{product_link}' target='_blank' 
                       style='color:#218c57;font-weight:bold;'>🔗 Xem chi tiết</a>
                </div>
                """

            info += "</div>"
            product_info.append(info)

        context = f"""
        Bạn là nhân viên tư vấn cho dịch vụ phòng trọ "The Fern House".
        Người dùng hỏi: {user_msg}

        Danh sách phòng trọ / sản phẩm phù hợp:
        {''.join(product_info)}

        👉 Hãy trả lời thân thiện, ngắn gọn, bằng tiếng Việt.
        - Nếu sản phẩm có nhiều lượt thích hoặc bình luận thì hãy nhấn mạnh điểm đó để khách yên tâm hơn.
        - Nếu có ảnh thì hiển thị ảnh (click được) và luôn có link "Xem chi tiết" ngay bên dưới ảnh.
        """
    else:
        context = f"""
        Bạn là nhân viên tư vấn cho dịch vụ phòng trọ "The Tiller House".
        Người dùng hỏi: {user_msg}

        Không tìm thấy phòng trọ hoặc sản phẩm phù hợp trong kho.
        👉 Hãy trả lời nhẹ nhàng, gợi ý khách hàng xem các lựa chọn khác
        (phòng diện tích khác, có/không nội thất, bàn ghế, giường, máy lạnh...).
        """

    return ask_gemini(context)
