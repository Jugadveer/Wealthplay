import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatMessage
from courses.models import Lesson


class LessonChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.lesson_id = self.scope['url_route']['kwargs']['lesson_id']
        self.room_group_name = f'lesson_{self.lesson_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')

        if message_type == 'message':
            sender = data.get('sender', 'user')
            text = data.get('text', '')
            time_display = data.get('time_display', '')

            # Save message to database
            message = await self.save_message(sender, text, time_display)

            # Broadcast to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'sender': message.sender,
                        'text': message.text,
                        'time_display': message.time_display,
                        'created_at': message.created_at.isoformat(),
                    }
                }
            )

            # TODO: Trigger AI response generation
            # This would call the LLM service and generate responses from Wise and Nex

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': message
        }))

    @database_sync_to_async
    def save_message(self, sender, text, time_display):
        try:
            lesson = Lesson.objects.get(id=self.lesson_id)
        except Lesson.DoesNotExist:
            return None

        message = ChatMessage.objects.create(
            lesson=lesson,
            sender=sender,
            text=text,
            time_display=time_display
        )
        return message





