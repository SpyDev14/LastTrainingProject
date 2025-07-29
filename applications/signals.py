from django.db.models.signals 	import post_save
from django.dispatch 			import receiver

from applications.models import Application, TelegramBot, TelegrammBotSendingSettings


@receiver(post_save, sender = Application)
def send_notification_into_telegramm_bot(sender, instance: Application, created, **kwargs):
	if not created:
		return

	settings = TelegrammBotSendingSettings.get_solo()
	bot: TelegramBot = settings.bot_for_notifications
	chat_id: str = settings.notifications_channel_id
	msg = f"""
<b>Новая заявка!</b>
Человек: {instance.requestener_name}
Населённый пункт: {instance.settlement}
Номер для связи: {instance.phone_number}
"""

	bot.send_telegram_message(chat_id, msg, parse_mode = "HTML")
