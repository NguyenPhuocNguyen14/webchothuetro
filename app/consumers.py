# app/consumers.py
import json
from datetime import datetime
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from .models import DirectChatMessage

User = get_user_model()

class DirectChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # room tương ứng với user_id trong URL (mỗi user có phòng riêng)
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f"chat_{self.user_id}"

        # group dành cho admin global notifications
        self.admin_group = "admin_notifications"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.channel_layer.group_add(self.admin_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_discard(self.admin_group, self.channel_name)

    async def receive(self, text_data):
        """
        Expect JSON payload, e.g.:
        {
          "message": "hello",
          "sender": "user" or "admin",
          "image_url": "https://..."   # optional
        }
        """
        try:
            data = json.loads(text_data)
        except Exception:
            return

        message = data.get("message", "") or ""
        sender = data.get("sender", "") or ""
        image_url = data.get("image_url")  # optional (string)

        # Lấy user (owner của phòng)
        user = await self._get_user(self.user_id)
        if not user:
            # nếu không tìm thấy user thì trả về lỗi nhẹ (không raise)
            await self.send(json.dumps({"error": "user_not_found"}))
            return

        # Lưu vào DB (async wrapper)
        created_msg = await sync_to_async(DirectChatMessage.objects.create)(
            user=user,
            sender=sender,
            message=message or None,
            image=image_url or None,
            is_read=False
        )

        # chuẩn metadata gửi cho frontend
        timestamp = datetime.utcnow().strftime("%H:%M %d/%m/%Y")
        snippet = (message[:140] + ("..." if len(message) > 140 else "")) if message else ""

        payload = {
            "type": "new_message",        # dùng để frontend dễ phân loại
            "id": created_msg.id,
            "user_id": str(self.user_id),
            "sender": sender,
            "message": message,
            "snippet": snippet,
            "image_url": image_url,
            "timestamp": timestamp,
        }

        # Gửi tới phòng của user (dành cho user hoặc admin đang mở phòng đó)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",   # maps to chat_message()
                "payload": payload
            }
        )

        # Gửi 1 thông báo tóm tắt tới admin group (admin dashboard có thể lắng nghe)
        admin_payload = {
            "type": "admin_notification",
            "user_id": str(self.user_id),
            "sender": sender,
            "snippet": snippet or ("📷 Ảnh" if image_url else ""),
            "timestamp": timestamp,
            "image_url": image_url,
        }
        await self.channel_layer.group_send(
            self.admin_group,
            {
                "type": "chat_message",
                "payload": admin_payload
            }
        )

    async def chat_message(self, event):
        """
        Mọi event group gửi tới đều đến đây, chỉ cần forward payload JSON cho client.
        """
        payload = event.get("payload", {})
        await self.send(text_data=json.dumps(payload))

    @staticmethod
    async def _get_user(user_id):
        try:
            return await User.objects.aget(id=user_id)
        except User.DoesNotExist:
            return None
