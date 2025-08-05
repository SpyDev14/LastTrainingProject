# Документация дублируется в документации PageRenderData
"""
Модуль для работы с регистрацией моделей в общий объект данных
передаваемых в контекст рендеринга Django-темплейтов
--------------------------------------------------------------
Используйте `register_model_for_page_render_data` как декоратор класса
**обычной**, или **синглтон** модели (`SingletonModel`), чтобы установить
итератор QuerySet по всем экземплярам модели, или единственный эклемпляр этой
модели в атрибуты класса `PageRenderData` соответственно. Атрибуты будут
иметь название `camel_to_snake_case($ClassName)` + `s`, если это итератор
обычных моделей (`QuerySet` объект), либо просто `camel_to_snake_case($ClassName)`,
если это единственный экземпляр Singleton-модели.
### Примеры названий:
- `class FAQPoint(Model)` -> <code>faq_point<b>s</b></code>
	(`QuerySet[FAQPoint]`)
- `class RegularModel(Model)` -> <code>regular_model<b>s</b></code>
	(`QuerySet[RegularModel]`)
- `class SiteSettings(SingletonModel)` -> `site_settings`
	(`<SiteSettings object at 0x...>`)
<br>

<small>Подробнее смотрите в документации <code>register_model_for_page_render_data
</code></small>
<hr>

Используйте `register_model_for_requirement_in_page_render_data_constructor`
как декоратор класса **обычной** модели, чтобы добавить экземпляр этой
модели в требуемые kwarg-и конструктора `PageRenderData`, после он будет
доступен через атрибут названия вида `camel_to_snake_case($ClassName)`. Название kwarg-а
будет эквивалентно названию атрибута.<br>
**Примеры названий:**
- `class FAQPoint(Model)` -> `faq_point`
	(`<FAQPoint object at 0x...>`)
- `class RegularModel(Model)` -> `regular_model`
	(`<RegularModel object at 0x...>`)
<br>
Попытка зарегистрировать синглтон-модель через этот метод вызовет ошибку.<br>
<small>Подробнее смотрите в документации <code>
register_model_for_requirement_in_page_render_data_constructor</code>
</small>
<hr>

Перед использованием `PageRenderData` его нужно инициализировать в
любом из методов `ready()` любого из классов конфига приложения,
выполнять инициализацию нужно **только один раз**:
```
class ...Config(AppConfig):
	def ready(self):
		from shared.rendering import render_data
		render_data.init_page_render_data_class()
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


_logger = logging.getLogger(__name__)

# Используется в register_model_for_page_render_data()
_models_for_render_data: set[type[Model]] = set()
# Используется в register_model_for_requirement_in_page_render_data_constructor
_required_models_for_render_data_constructor: dict[str, type[Model]] = {}

_inited: bool = False
_required_kwarg_names: set[str] | None = None # Используется в конструкторе, это для оптимизации

def register_model_for_page_render_data(cls: type[SingletonModel]):
	# Документация частично дублируется в документации модуля
	"""
	Добавляет класс модели в список, на основе которого при запуске серврера будет создан
	и помещён в атрибуты класса `PageRenderData` единственный синглтон-экземпляр модели,
	если это сингтон-модель (`SingletonModel`), или итератор `QuerySet` всех экземпляров модели
	(`objects.all()`), если это обычная модель.
	Атрибуты с итераторами обычных моделей (`QuerySet`) будут иметь название вида
	`camel_to_snake_case($ClassName)` + постфикс `s`.
	Атрибуты с единственными экземплярами синглтон-моделей будут иметь название вида
	`camel_to_snake_case($ClassName)`, без дополнительных изменений.<br>
	
	### Примеры названий:
	- `class FAQPoint(Model)` -> <code>faq_point<b>s</b></code>
		(`QuerySet[FAQPoint]`)
	- `class RegularModel(Model)` -> <code>regular_model<b>s</b></code>
		(`QuerySet[RegularModel]`)
	- `class SiteSettings(SingletonModel)` -> `site_settings`
		(`<SiteSettings object at 0x...>`)
	<br>

	### Пример использования:
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

def register_model_for_requirement_in_page_render_data_constructor(cls: type[Model]):
	# Документация частично дублируется в документации модуля
	"""
	Используйте этот метод как декоратор класса **обычной** модели, чтобы добавить экземпляр
	этой модели в требуемые kwarg-и конструктора `PageRenderData`, после он будет
	доступен через атрибут названия вида `camel_to_snake_case($ClassName)`. Название kwarg-а
	будет эквивалентно названию атрибута.<br>

	### Примеры названий:
	- `class FAQPoint(Model)` -> `faq_point`
		(`<FAQPoint object at 0x...>`)
	- `class RegularModel(Model)` -> `regular_model`
		(`<RegularModel object at 0x...>`)<br>

	Попытка зарегистрировать синглтон-модель через этот метод вызовет ошибку.<br>

	### Пример использования:
	```
	@register_model_for_requirement_in_page_render_data_constructor
	class MyModel(Model): ...

	# TypeError: MySingletonModel is a SingletonModel. Use register_model_for_page_render_data instead.
	@register_model_for_requirement_in_page_render_data_constructor
	class MySingletonModel(SingletonModel): ...
	```

	### Пример создания объекта `PageRenderData` после регистрации модели через этот метод:
	```
	data = PageRenderData(
		my_model = my_model_instance
	)
	print(data.my_model)
	# <MyModel object at 0x...> # Экземпляр модели
	data.my_model is my_model_instance # True

	### Без передачи в конструктор
	data = RageRenderData()
	# TypeError: Missing required models: my_model
	```

	Raises:
		RuntimeError:
			- Модель уже зарегистрирована

		TypeError:
			- Это не дочерний класс `Model`
			- Это синглтон-модель
	"""
	if camel_to_snake_case(cls.__name__) in _required_models_for_render_data_constructor:
		raise RuntimeError(f"{cls.__name__} already registered.")
	if not issubclass(cls, Model):
		raise TypeError(f"{cls.__name__} must be a subclass of Model.")
	if issubclass(cls, SingletonModel):
		raise TypeError(f"{cls.__name__} is a SingletonModel. Use register_model_for_page_render_data instead.")
	
	_required_models_for_render_data_constructor[camel_to_snake_case(cls.__name__)] = cls
	return cls

# TODO: для оптимизации можно релизовать "lazy-метод" и устанавливать значение в атрибут
# в __getattr__ при первом обращении, а после возвращать значение из этого атрибута.
# Тогда надобность в регистрации при запуске сервера отпадёт сама собой.
class PageRenderData:
	# Документация дублируется в документации модуля
	"""
	Общий объект данных передаваемых в контекст рендеринга Django-темплейтов<br>
	------------------------------------------------------------------------
	Используйте `register_model_for_page_render_data` как декоратор класса
	**обычной**, или **синглтон** модели (`SingletonModel`), чтобы установить
	итератор QuerySet по всем экземплярам модели, или единственный эклемпляр этой
	модели в атрибуты класса `PageRenderData` соответственно. Атрибуты будут
	иметь название `camel_to_snake_case($ClassName)` + `s`, если это итератор
	обычных моделей (`QuerySet` объект), либо просто `camel_to_snake_case($ClassName)`,
	если это единственный экземпляр Singleton-модели.
	### Примеры названий:
	- `class FAQPoint(Model)` -> <code>faq_point<b>s</b></code>
		(`QuerySet[FAQPoint]`)
	- `class RegularModel(Model)` -> <code>regular_model<b>s</b></code>
		(`QuerySet[RegularModel]`)
	- `class SiteSettings(SingletonModel)` -> `site_settings`
		(`<SiteSettings object at 0x...>`)
	<br>

	<small>Подробнее смотрите в документации <code>register_model_for_page_render_data
	</code></small>
	<hr>

	Используйте `register_model_for_requirement_in_page_render_data_constructor`
	как декоратор класса **обычной** модели, чтобы добавить экземпляр этой
	модели в требуемые kwarg-и конструктора `PageRenderData`, после он будет
	доступен через атрибут названия вида `camel_to_snake_case($ClassName)`. Название kwarg-а
	будет эквивалентно названию атрибута.<br>
	**Примеры названий:**
	- `class FAQPoint(Model)` -> `faq_point`
		(`<FAQPoint object at 0x...>`)
	- `class RegularModel(Model)` -> `regular_model`
		(`<RegularModel object at 0x...>`)
	<br>
	Попытка зарегистрировать синглтон-модель через этот метод вызовет ошибку.<br>
	<small>Подробнее смотрите в документации <code>
	register_model_for_requirement_in_page_render_data_constructor</code>
	</small>
	<hr>

	Перед использованием `PageRenderData` его нужно инициализировать в
	любом из методов `ready()` любого из классов конфига приложения,
	выполнять инициализацию нужно **только один раз**:
	```
	class ...Config(AppConfig):
		def ready(self):
			from shared.rendering import render_data
			render_data.init_page_render_data_class()
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



def init_page_render_data_class():
	# Документация частично дублируется в документации модуля
	"""
	Перед использованием `PageRenderData` его нужно инициализировать
	этим методом в любом из методов `ready()` любого из классов конфига
	приложения, выполнять инициализацию нужно **только один раз**:
	```
	class ...Config(AppConfig):
		def ready(self):
			from shared.rendering import render_data
			render_data.init_page_render_data_class()
	```

	Raises:
		RuntimeError:
			- Попытка вызвать второй раз
	"""
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
		# Не работает на 3.11
		f"\033[32mPageRenderData\033[0m initialization successful completed.\n"
		f"\033[36mModels\033[0m: \n > {
			'\n > '.join(
				f"{model.__name__} as {(
					camel_to_snake_case(model.__name__) +
					('s' if not issubclass(model, SingletonModel) else '')
				)}"
				for model in _models_for_render_data
			)
		}"
		f"\n\n"
		f"\033[34mModels for requirement in constructor kwargs\033[0m: \n > {
			'\n > '.join(
				f"{model.__name__} as {arg_name}"
				for arg_name, model in _required_models_for_render_data_constructor.items()
			)
		}"
		f"\n"
	)
