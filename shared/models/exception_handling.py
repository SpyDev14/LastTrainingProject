from logging import Logger

from django.db.models 		import Model
from django.db.utils 		import OperationalError

class HandleAndLogNotMigratedModelError:
	"""
	Ловит исключение, возникающее если происходит обращение к модели не прошедшей миграцию.
	Логгирует, если был передан логгер.

	Можно указать дополнительно сообщение для логгера, уточняющее что следует из этой ошибки.<br>
	**По умолчанию:**<br>
	`Миграции для модели "{type(self._model).__name__}" не были произведены.`<br>
	**С комментарием:**<br>
	`Миграции для модели "{type(self._model).__name__}" не были произведены, {error_comment}.`
	"""
	def __init__(
			self,
			model: type[Model],
			*,
			logger: Logger | None = None,
			error_comment: str | None = None):
		self._model = model
		self._logger = logger

		# это удобнее чем всё сообщение целиком с %s для последующей подстановки типа модели
		self._error_comment = error_comment 

	def __enter__(self):
		return self
	
	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type is not OperationalError:\
			return False

		if not str(exc_value).startswith("no such"):
			return False

		if self._logger:
			self._logger.error(
				f'Обнаружена попытка доступа к модели "{self._model.__name__}", для которой не проведены миграции' +
				f", {self._error_comment}." if self._error_comment else '.'
			)
		return True
