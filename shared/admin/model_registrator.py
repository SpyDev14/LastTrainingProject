from logging import Logger

from django.contrib.admin 	import ModelAdmin, site
from django.db.models 		import Model
from django.db.utils 		import OperationalError
from django.apps 			import apps

from ordered_model.models 	import OrderedModel
from ordered_model.admin 	import OrderedModelAdmin
from solo.models 			import SingletonModel

from shared.admin.singleton_utils 		import make_singleton_model_admin_class
from shared.models.exception_handling 	import HandleAndLogNotMigratedModelError


class AdminModelRegistrator:
	def __init__(self,
			app_name: str,
			*,
			logger: Logger | None = None,
			excluded_models: set[type[Model]] = set(),
			custom_admin_classes_for_models: dict[type[Model], type[ModelAdmin]] = dict()):
		self._app_name: str = app_name
		self._excluded_models: set[type[Model]] = excluded_models
		self._custom_admin_classes_for_models: dict[type[Model], type[ModelAdmin]] = custom_admin_classes_for_models

		self._logger: Logger | None = logger

	def exclude_model(self, model: type[Model]):
		self._excluded_models.add(model)

	def exclude_models(self, models: set[type[Model]]):
		self._excluded_models.update(models)

	def set_custom_admin_class_for_model(self, model: type[Model], admin_class: type[ModelAdmin]):
		self._custom_admin_classes_for_models[model] = admin_class

	def set_for_model(self, model: type[Model]):
		def decorator(admin_class: type[ModelAdmin]):
			self.set_custom_admin_class_for_model(model, admin_class)
			return admin_class
		
		return decorator


	def register(self):
		for model in apps.get_app_config(self._app_name).get_models():
			if model in self._excluded_models:
				continue
			if model == SingletonModel:
				continue

			admin_class: ModelAdmin | None = None
			ERROR_MSG = "Миграции для модели %s не были произведены, " \
						"регистрация в админ панели пропущена."

			with HandleAndLogNotMigratedModelError(model, logger = self._logger, error_comment = ERROR_MSG):
				if model in self._custom_admin_classes_for_models:
					admin_class = self._custom_admin_classes_for_models[model]

				elif issubclass(model, SingletonModel):
					admin_class = make_singleton_model_admin_class(model)

				elif issubclass(model, OrderedModel):
					admin_class = OrderedModelAdmin

				site.register(model, admin_class)
"""
			try:

			# Миграции не выполнены, без этого при ЛЮБОМ вызове manage.py будет ошибка
			# Ps: логи не выводятся во время миграций и т.п
			except OperationalError as e:
				if not str(e).startswith("no such table"):
					raise

				if self._logger:
					self._logger.error(
						f"Миграции для модели {model.__name__} не были произведены,"
						" регистрация в админ панели пропущена."
					)
"""
