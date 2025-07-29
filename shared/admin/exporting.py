from datetime 	import date
from typing 	import Iterable, Sequence, Callable, Any
from io 		import BytesIO

from django.db.models 	import QuerySet, Model
from django.http 		import FileResponse

from openpyxl.worksheet.worksheet import Worksheet
from phonenumbers 	import format_number, PhoneNumberFormat, PhoneNumber
from pandas 		import DataFrame, ExcelWriter


# TODO: лучше разбить на кучу мелких подфункций для улучшения читаемости.
# (пусть они и не будут нужны ни для чего, кроме использования здесь)
def export_to_excel(
	queryset: QuerySet,
	filename: str,
	*,
	sheet_name: str | None = "Данные",
	max_cells_check: int = 20,
	fields: Sequence[str] | None = None,
	verbose_names: Sequence[str | None] | None = None,
	date_format: str = '%d.%m.%Y %H:%M',
	formatters: dict[str, Callable[[Any], Any]] | None = None) -> FileResponse:
	"""
	Экспорт QuerySet в Excel, возвращает HTTPRequest с файлом для скачивания.
	Не будет экспортировать поля один ко многим.

	Args:
		queryset: QuerySet для экспорта.
		filename: Имя файла для экспорта.
		sheet_name: Название листа в Excel (По умолчанию "Данные").
		max_cells_check:
			Максимальное количество первых клеток для подсчёта
			ширины столбца, минимум 1.
		fields: Список полей модели (если None — все поля).
		verbose_names:
			Читаемые названия колонок (соответствуют fields).
			Если не задано - будут использованы verbose_names из данных модели.
			При указании None в качестве эелемента - для поля по этому индексу
			будет выбрано значение по умолчанию.
			Здесь можно было использовать dict, но я до этого догадался уже когда всё сделал.
		date_format: Формат дат (по умолчанию 'дд.мм.гггг чч:мм').
		formatters: Словарь {поле: функция_форматирования(значение поля) ->
			форматированое значение поля (предпочтительно строка)}.

	Returns:
		HttpResponse с файлом Excel.

	Raises:
		ValueError:
			- max_cells_check < 1
			- fields содержит несуществующие поля.
			- Длина fields & verbose_names (если последние указанны) не совпадают.
	"""
	# MARK: ВАЛИДАЦИЯ
	if max_cells_check < 1:
		raise ValueError("Max cells check cannot be less 1")

	if verbose_names and len(verbose_names) != len(fields):
		raise ValueError("verbose_names length must match fields")
	
	# MARK: ИНИЦИАЛИЗАЦИЯ
	model_class: Model = queryset.model # для аннотации
	model_meta = model_class._meta
	del model_class

	if fields is not None:
		for field_name in fields:
			if not model_meta.get_field(field_name):
				raise ValueError(f"Field {field_name} does not exist")

	# Поля для экспорта
	else:
		fields = (field.name for field in model_meta.fields)


	# Кастомные форматтировщики
	formatters = formatters or {}

	# Названия колонок
	if verbose_names is None:
		verbose_names = [
			model_meta.get_field(field_name).verbose_name
			for field_name in fields
		]
	else:
		for i, (field_name, verbose_name) in enumerate(zip(fields, verbose_names)):
			if verbose_name is None:
				verbose_names[i] = model_meta.get_field(field_name).verbose_name


	# MARK: ФОРМИРОВАНИЕ ДАННЫХ
	data: list[dict[str, Any]] = []
	for instance in queryset:
		row: dict[str, Any] = {}

		for field_name, verbose_name in zip(fields, verbose_names):
			value = getattr(instance, field_name)

			# Раньше обработка была сложнее, но я упростил
			if field_name in formatters:
				value = formatters[field_name](value)
			elif isinstance(value, date):
				value = value.strftime(date_format)
			elif isinstance(value, Model):
				value = str(value)
			elif isinstance(value, PhoneNumber):
				value = format_number(value, PhoneNumberFormat.INTERNATIONAL)

			# Может не пройти никакой обработки
			row[verbose_name] = value or ""

		data.append(row)


	# MARK: ГЕНЕРАЦИЯ ФАЙЛА
	data_frame = DataFrame(data)
	buffer = BytesIO() # В памяти
	# Также можно сразу писать в HttpResponse, но так удобне

	with ExcelWriter(buffer, engine = 'openpyxl') as writer:
		data_frame.to_excel(
			writer,
			index = False,
			sheet_name = sheet_name
		)

		worksheet: Worksheet = writer.sheets[sheet_name]

		for column in worksheet.columns:
			# column_letter - колонка в Excel: A, B, C, D...
			column_letter = column[0].column_letter

			max_cell_width = max(
				len(str(cell.value)) if cell.value else 0
				for cell in column[:max_cells_check]
			)
			worksheet.column_dimensions[column_letter].width = max_cell_width + 2 # (С запасом)

	# Подготавливаем буффер для чтения: устанавливаем курсор в начало
	buffer.seek(0)

	return FileResponse(
		buffer,
		filename = f"{filename}.xlsx",
		as_attachment = True,
		content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
	)
