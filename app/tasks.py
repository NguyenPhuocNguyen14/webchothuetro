# app/tasks.py
import time
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task(bind=True)
def test_task(self, x=1):
    print(">>> test_task started (worker)", getattr(self.request, "hostname", "unknown"))
    time.sleep(1)
    print(">>> test_task finished ✅ - arg:", x)
    return f"ok {x}"

@shared_task(bind=True)
def send_contact_email(self, subject, message, from_email, to_email=None):
    """
    Gửi email contact ở background.
    - subject, message, from_email: từ form contact.
    - to_email: nếu None sẽ dùng settings.CONTACT_EMAIL hoặc settings.DEFAULT_FROM_EMAIL
    Trả về dict {ok: True/False, error: ...}
    """
    to = to_email or getattr(settings, "CONTACT_EMAIL", settings.DEFAULT_FROM_EMAIL)
    try:
        # send_mail trả về số email sent (int)
        sent = send_mail(subject, message, from_email, [to], fail_silently=False)
        return {"ok": True, "sent": sent}
    except Exception as e:
        # log rõ ra console để worker show
        print(">>> send_contact_email error:", repr(e))
        return {"ok": False, "error": str(e)}
