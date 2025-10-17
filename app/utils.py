import google.generativeai as genai
from django.conf import settings
import logging

# Cấu hình Gemini với API key trong settings
genai.configure(api_key=settings.GEMINI_API_KEY)

def ask_gemini(prompt: str) -> str:
    """Gọi Gemini model để trả lời prompt"""
    try:
        # ⚡ Dùng model mới (ổn định hơn)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)

        # Nếu Gemini trả về text hợp lệ
        if response and hasattr(response, "text") and response.text:
            return response.text.strip()

        return "❌ Xin lỗi, hiện tại mình chưa nhận được phản hồi từ AI. Bạn có thể thử lại sau nhé!"
    
    except Exception as e:
        logging.error(f"Gemini API error: {e}")

        err = str(e).lower()
        if "429" in err or "quota" in err:
            return "⚠️ Server AI đang quá tải hoặc hết lượt trong ngày. Bạn vui lòng thử lại sau nhé!"
        elif "404" in err:
            return "⚠️ Model AI không tồn tại hoặc không được hỗ trợ. Vui lòng kiểm tra lại tên model!"
        else:
            return "❌ Có lỗi xảy ra khi kết nối AI. Vui lòng thử lại sau!"
