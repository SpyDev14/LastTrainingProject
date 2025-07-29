import re
from django.core.exceptions import ValidationError

def env_variable_name_validator(value: str):
	_VALID_REGEX_FORMAT: str = r'^[A-Z_][A-Z0-9_]*$'
	valid: bool = re.fullmatch(_VALID_REGEX_FORMAT, value) is not None

	if not valid:
		raise ValidationError(
			"Это не валидное имя для Enviroment переменной, "
			"разрешены только буквы в верхнем регистре, нижние "
			"подчёркивания и цифры, но название не может начинаться с цифры."
		)

def string_is_correct_numeric_validator(value: str):
	if not isinstance(value, str):
		raise TypeError("Not a string")
	try:
		int(value)
	except ValueError:
		raise ValidationError("Эта строка должна соответствовать целому числу")

# Функция верная, но в публиные каналы отправлять всё же врядли нужно
def telegramm_chat_id_validator(value: str):
	_VALID_REGEX_FORMAT: str = r'^@[a-zA-Z0-9_]{5,32}$'
	try:
		string_is_correct_numeric_validator(value)
		return
	except:
		pass

	valid: bool = re.fullmatch(_VALID_REGEX_FORMAT, value) is not None
	if not valid:
		raise ValidationError(
			"Это некорректный ID телеграм чата."
		)
