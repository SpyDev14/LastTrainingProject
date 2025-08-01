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
		from shared.rendering import render_data
		render_data._init_page_render_data_class()
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


# TODO: Вместо переменных и функций на уровне модуля лучше использовать специальный класс PageRenderDataController
# UPD: Я думаю, что класс всё же будет излишним, но я оставлю эту идею здесь на всякий случай
_logger = logging.getLogger(__name__)

# Экземпляры этих моделей будут требоваться в конструкторе при создании
_required_models_for_render_data_constructor: dict[str, type[Model]] = {}
# Итератор экземпляров стандартных моделей будет помещён в атрибуты класса с постфиксом s
# Эксемпляр синглтон моделей будет помещён в атрибуты класса
_models_for_render_data: set[type[Model]] = set()

_inited: bool = False
_required_kwarg_names: set[str] | None = None # Используется в конструкторе, это для оптимизации

def register_model_for_requirement_in_page_render_data_constructor(cls: type[Model]):
	"""
	Добавляет класс модели в список требуемых для создания объекта данных для рендеринга
	html-страниц, где переданный экземпляр будет доступен по названию своей модели.

	Пример создания объекта `PageRenderData` после регистрации модели через этот метод:
	```
	data = PageRenderData(
		my_model = my_model_instance
	)
	print(data.my_model)
	# <$MY_MODEL object at 0x...> # Экземпляр модели
	data.my_model is my_model_instance # True

	### Без передачи в конструктор
	data = RageRenderData()
	# TypeError: Missing required models: my_model
	```
	"""
	if camel_to_snake_case(cls.__name__) in _required_models_for_render_data_constructor:
		raise ValueError(f"{cls.__name__} already registered.")
	if not issubclass(cls, Model):
		raise TypeError(f"{cls.__name__} must be a subclass of Model.")
	if issubclass(cls, SingletonModel):
		raise TypeError(f"{cls.__name__} is a SingletonModel. Use register_model_for_page_render_data instead.")
	
	_required_models_for_render_data_constructor[camel_to_snake_case(cls.__name__)] = cls
	return cls

def register_model_for_page_render_data(cls: type[SingletonModel]):
	"""
	Добавляет класс модели в список на основе которого при запуске серврера будет создан
	и помещён в атрибуты класса, используемого для рендеринга html-страниц, синглтон-экземпляр,
	если это сингтон-модель, или итератор экземпляров (`objects.all()`), если это обычная модель,
	который будет находится в атрибуте вида `camel_to_snake_case($CLASS)s`, то есть
	`FAQPoint -> faq_points`.

	Пример использования:
	- **models.py**
	```
	@register_model_for_page_render_data
	class Post(Model):
		...

	@register_model_for_page_render_data
	class CompanyContacts(SingletonModel):
		...
	```
	- **views.py**
	```
	data = PageRenderData()
	print(data.posts) # <QuerySet object at 0x...> # Тип: QuerySet[Post]
	print(data.company_contacts) # <CompanyContacts object at 0x...>
	```
	"""
	if not issubclass(cls, Model): raise TypeError(f"{cls.__name__} must be a subclass of Model")
	_models_for_render_data.add(cls)
	return cls


# TODO: для оптимизации можно релизовать "lazy-метод" и устанавливать значение в атрибут
# в __getattr__ при первом обращении, а после возвращать значение из этого атрибута.
class PageRenderData:
	"""
	Общий объект данных для передачи в контекст при редеринге HTML-страниц.<br>
	---------------------------------------------------------------------------
	**Единственные экземпляры** помеченных **синглтон-моделей** (`SingletonModel`) будут динамически
	помещены в атрибуты этого класса при старте сервера.<br>

	**Итераторы** (`objects.all()`) зарегистрированных **обычных моделей**(`Model`) будут динамически
	помещены в атрибуты этого класса с названием вида `camel_to_snake_case($CLASS)s`, то есть
	`FAQPoint -> faq_points`, `Post -> posts`.

	<small>Подробнее смотрите в документации `register_model_for_page_render_data()`</small>
	<hr>
	
	Экземпляры **стандартных моделей**(`Model`) помеченых как требуемые в конструкторе
	будут требоваться в конструкторе при создании и будут доступны через атрибут вида
	`camel_to_snake_case($CLASS)`.

	<small>Подробнее смотрите в документации
	`register_model_for_requirement_in_page_render_data_constructor()`</small>
	<hr>

	Пример использования:
	- **models.py**
	```
	import render_data

	@render_data.register_model_for_requirement_in_page_render_data_constructor
	class Page(Model): ...

	@render_data.register_model_for_page_render_data
	class FAQPoint(Model): ...

	@render_data.register_model_for_page_render_data
	class SiteSettings(SingletonModel): ...
	```
	- **views.py**
	```
	class MainView(View):
		def get(self, request):
			...
			data = PageRenderData(page = page_instance)
			context = {'data': data}

			print(object.__str__(data.page))
			# <Page object at ...>

			print(object.__str__(data.site_settings))
			# <SiteSettings object at ...>

			print(object.__str__(data.faq_points))
			# <QuerySet object at ...> # Тип: QuerySet[FAQPoint]

			return render(request, ..., context)
	```
	
	Raises:
		TypeError:
			- Необходимые аргументы отстутствуют
			- Присутствуют лишние аргументы
			- Тип переданного объекта не соответствует запрашиваемому.
		RuntimeError: не инициализированно, инициализируйте в любом из `AppConfig.ready()`
			через `_init_page_render_data_class()`.
	"""
	def __init__(self, **kwargs: dict[str, Model]):
		if not _inited:
			raise RuntimeError("PageRenderData not inited yet")

		# Переданы только запрашиваемые модели
		actual_args: set[str] = set(kwargs)
		if missing_args := _required_kwarg_names - actual_args:
			raise TypeError(f"Missing required models: {', '.join(missing_args)}")

		if extra_args := actual_args - _required_kwarg_names:
			raise TypeError(f"Unexpected extra models: {', '.join(extra_args)}")

		for arg_name, value in kwargs.items():
			# Проверка типа
			required_model_cls = _required_models_for_render_data_constructor[arg_name]

			if not isinstance(value, required_model_cls):
				raise TypeError(
					f"Model type `{required_model_cls.__name__}` was expected, "
					f"but `{type(value).__qualname__}` was received."
				)
			setattr(self, arg_name, value)


# Вызывается в ready (когда все модели загружены)
def _init_page_render_data_class():
	global _inited
	if _inited:
		raise RuntimeError("Already inited")

	for model in _models_for_render_data:
		if not issubclass(model, Model):
			raise TypeError

		with HandleAndLogNotMigratedModelError(model,logger=_logger,error_comment="регистрация в PageRenderData пропущена"):
			update_handler: Callable | None = None

			if issubclass(model, SingletonModel):
				setattr(
					PageRenderData,
					camel_to_snake_case(model.__name__),
					model.get_solo()
				)

				def _singleton_update_handler(sender, instance, *args, **kwargs):
					setattr(PageRenderData, camel_to_snake_case(model.__name__), instance)
					_logger.debug(f'PageRenderData model {type(instance).__name__} updated.')
				update_handler = _singleton_update_handler

			else:
				setattr(
					PageRenderData,
					f"{camel_to_snake_case(model.__name__)}s", # в конец добавляется `s`!
					model.objects.all()
				)
				def _update_handler(sender, instance, *args, **kwargs): # в конец добавляется `s`!
					setattr(PageRenderData, f"{camel_to_snake_case(model.__name__)}s", model.objects.all())
					_logger.debug(f'PageRenderData model {type(instance).__name__} updated.')
				update_handler = _update_handler
				# Также независимо от этого места название ('s'/'') расчитывается в логах
			receiver(post_save, sender = model)(update_handler)
	


	global _required_kwarg_names
	# Можно было бы добавлять элементы сразу в методе регистрации, но так будет надёжней
	# Это для оптимизации, чтобы не высчитывать каждый раз в __init__, так как эти значения не меняются.
	_required_kwarg_names = set(_required_models_for_render_data_constructor) # keys

	_inited = True
	_logger.debug(
		"\033[32mPageRenderData\033[0m initialization successful completed.\n"
		f"\033[36mModels\033[0m: \n > {
			'\n > '.join(
				f"{model.__name__} as {
					camel_to_snake_case(model.__name__) +
					('s' if not issubclass(model, SingletonModel) else '')
				}"
				for model in _models_for_render_data
			)
		}"
		"\n\n"
		f"\033[34mModels for requirement in constructor kwargs\033[0m: \n > {
			'\n > '.join(
				f"{model.__name__} as {arg_name}"
				for arg_name, model in _required_models_for_render_data_constructor.items()
			)
		}"
		"\n"
	)
