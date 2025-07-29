from typing import Literal
from os 	import getenv
import requests, logging

from django.db import models

from phonenumber_field.modelfields 	import PhoneNumberField
from solo.models 					import SingletonModel

from shared.models.validators import env_variable_name_validator, telegramm_chat_id_validator, string_is_correct_numeric_validator


_logger = logging.getLogger(__name__)

class Application(models.Model):
	requestener_name = models.CharField(verbose_name = "Имя", max_length = 24)
	settlement = models.CharField(verbose_name = "Населённый пункт", max_length = 64)
	phone_number = PhoneNumberField(verbose_name = "Номер телефона")
	date = models.DateTimeField(verbose_name = "Дата заполнения заявки",auto_now_add = True, editable = False)

	class Meta:
		verbose_name = 'Заявка'
		verbose_name_plural = 'Заявки'

	def __str__(self):
		return f'{self.requestener_name} {self.phone_number} из {self.settlement}'

class TelegramBot(models.Model):
	assignment = models.CharField(verbose_name = "Предназначен для", help_text = "Ни на что не влияет", max_length = 512)
	token_env_variable_name = models.CharField(
		verbose_name = "ENV-переменная с токеном",
		unique = True, max_length = 128, validators = [env_variable_name_validator])
	
	class Meta:
		verbose_name = "Телеграм бот"
		verbose_name_plural = "Телеграм боты"
	def __str__(self):
		return f"Телеграм бот для {self.assignment}"
	
	def send_telegram_message(self, chat_id: str, text: str, *, parse_mode: Literal["HTML", "MarkdownV2"] | None) -> bool:
		"""
		Отправляет сообщение через телеграм бота.
		Args:
			token: токен бота
			chat_id: ID чата в формате числа, либо @chat_id
			text: Сообщение
			parse_mode: строка с типом режима парсинга сообщения, согласно документации.
		Returns:
			Успешно или нет.
		"""
		token = getenv(self.token_env_variable_name)
		if not token:
			return False

		url = f"https://api.telegram.org/bot{token}/sendMessage"
		payload = {
			"chat_id": chat_id,
			"text": text
		}
		if parse_mode:
			payload['parse_mode'] = parse_mode

		try:
			# FIXME: Выводит в debug url с токеном бота!!!
			response = requests.post(url, json = payload)
			response.raise_for_status()
		except requests.exceptions.RequestException as e:
			_logger.error(
				f"Ошибка при отправке сообщения телеграм ботом "
				f"(code {e.response.status_code}): {e.response.text}")
			return False

		return True


# MARK: Singleton models
# Немного глупая получилась система, просто вынес название ENV-переменной в отдельную модель.
class TelegrammBotSendingSettings(SingletonModel):
	bot_for_notifications = models.OneToOneField(TelegramBot, on_delete = models.SET_NULL, null = True, blank = True,
		verbose_name = "Телеграм бот для отправки уведомления")

	notifications_channel_id = models.CharField(blank = True, max_length = 64,
		validators = [string_is_correct_numeric_validator],
		verbose_name = "ID чата для отправки уведомления", 
		help_text = "Либо число, либо отрицательное число для группы, согласно документации telegram."
	)

	class Meta:
		verbose_name = "Настройки Telegram уведомлений"
		verbose_name_plural = "Настройки Telegram уведомлений"
	def __str__(self): return "Настройки Telegram уведомлений"
