"""
Регистрации моделей для добавления в общий объект контекста
для django template рендеринга html:
------------------------------------------------------------
```
@register_singleton_model_for_page_render_data
class SiteConfig(SingletonModel):
	...

@register_model_for_requirement_in_page_render_data_constructor
class UserProfile(Model):
	...
```
Инициализация (в apps.py; в единственном месте):
```
class ...Config(AppConfig):
	def ready(self):
		_init_page_render_data_class()
```
"""

from typing import Callable
import logging

from django.db.models.signals 	import post_save
from django.db.models		 	import Model
from django.dispatch 			import receiver
from solo.models 				import SingletonModel

from shared.models.exception_handling 	import HandleAndLogNotMigratedModelError
from shared.string_processing.cases 	import camel_to_snake_case




class PageRenderData:
	"""
	Общий объект данных для передачи в контекст при редеринге Html-страниц.<br>

	Единственные экземпляры помеченных синглтон-моделей будут динамически
	помещены в атрибуты этого класса при старте сервера.<br>

	Итераторы (`objects.all()`) зарегистрированных обычных моделей будут динамически помещены
	в атрибуты этого класса с названием вида `camel_to_snake_case(CLASS)s`, то есть
	`FAQPoint -> faq_points`

	Экземпляры стандартных моделей помеченых как требуемые будут требоваться
	в конструкторе при создании и будут доступны через атрибут вида `camel_to_snake_case(CLASS)`.

	:raise TypeError: Необходимые аргументы отстутствуют, присутствуют лишние аргументы,
		либо тип переданного объекта не соответствует запрашиваемому.
	:raise RuntimeError: не инициализированно, инициализируйте в `ready()` через `_init_page_render_data_class()`.
	"""
	def __init__(self, **kwargs: dict[str, Model]):
		if not PRDController._inited:
			raise RuntimeError("PageRenderData not inited yet")

		# Переданы только запрашиваемые модели
		actual_args: set[str] = set(kwargs)
		if missing_args := PRDController._required_kwarg_names - actual_args:
			raise TypeError(f"Missing required models: {', '.join(missing_args)}")

		if extra_args := actual_args - PRDController._required_kwarg_names:
			raise TypeError(f"Unexpected extra models: {', '.join(extra_args)}")

		for arg_name, value in kwargs.items():
			# Проверка типа
			if arg_name in PRDController._required_models_for_render_data_constructor:
				required_model_cls = PRDController._required_models_for_render_data_constructor[arg_name]

				if not isinstance(value, required_model_cls):
					raise TypeError(
						f"Model type `{required_model_cls.__name__}` was expected, "
						f"but `{type(value).__qualname__}` was received."
					)
			setattr(self, arg_name, value)

class PRDController:
	_inited: bool = False
	_required_kwarg_names: set[str] = set() # Вычислим единожды, для оптимизации

	_registered_models_for_requirement_in_constructor: \
		dict[str, type[Model]] = {}
	_registered_models: set[type[Model]] = set()

	@staticmethod
	def _make_standart_model_iterator_attr_name(model_class: type[Model]):
		return f"{camel_to_snake_case(model_class.__name__)}s"

	# Обработчики
	@staticmethod
	def _singleton_model_update_handler():
		pass
	@staticmethod
	def _model_update_handler():
		pass

	@staticmethod
	def register_model(cls):
		pass
	@staticmethod
	def register_model_for_requirement_in_constructor(cls):
		pass

	@classmethod
	def init_page_render_data_class(cls):
		pass
