# app/tasks.py
import time
from celery import shared_task

@shared_task(bind=True)
def test_task(self, x=1):
    """Task test: log, sleep 1s, trả về 'ok <x>'."""
    # Lưu ý: self.request.hostname chứa thông tin worker instance
    print(">>> test_task started (worker)", getattr(self.request, "hostname", "unknown"))
    time.sleep(1)
    print(">>> test_task finished ✅ - arg:", x)
    return f"ok {x}"
