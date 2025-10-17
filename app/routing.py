from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Mỗi user sẽ có phòng chat riêng với admin, theo user_id
    re_path(r"ws/chat/(?P<user_id>\d+)/$", consumers.DirectChatConsumer.as_asgi()),
]
