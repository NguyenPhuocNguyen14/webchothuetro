document.addEventListener('DOMContentLoaded', function () {
    const updateBtns = document.querySelectorAll('.update-cart');

    updateBtns.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault(); // tránh reload trang nếu nút trong form

            const productId = this.dataset.product;
            const action = this.dataset.action;

            console.log('👉 productId:', productId, '| action:', action);
            console.log('👤 user:', user);

            if (user === "AnonymousUser") {
                alert("⚠️ Bạn cần đăng nhập để thêm vào giỏ hàng!");
                window.location.href = "/login/";
            } else {
                console.log("✅ User đã đăng nhập, gọi API thêm giỏ hàng...");

                fetch("/update_item/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrftoken,
                    },
                    body: JSON.stringify({
                        "productId": productId,
                        "action": action,
                    }),
                })
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP lỗi! status: ${response.status}`);
                    return response.json();
                })
                .then(data => {
                    console.log("📦 Kết quả từ server:", data);

                    // Cập nhật số lượng sản phẩm trên trang
                    const qtyElem = document.querySelector(`#qty-${productId}`);
                    if (qtyElem) qtyElem.textContent = data.quantity;

                    // Cập nhật tổng tiền giỏ hàng
                    const totalElem = document.querySelector('#cart-total');
                    if (totalElem && data.cart_total !== undefined) {
                        totalElem.textContent = data.cart_total.toLocaleString('vi-VN') + ' VNĐ';
                    }
                })
                .catch(error => {
                    console.error("❌ Lỗi khi update cart:", error);
                    alert("Có lỗi xảy ra khi thêm sản phẩm vào giỏ!");
                });
            }
        });
    });
});
