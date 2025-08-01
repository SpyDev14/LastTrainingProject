from functools import cached_property
from pathlib import Path
import logging

from django.http 			import HttpRequest
from django.shortcuts 		import render, redirect
from django.views 			import View

from applications.forms import ApplicationForm
from content 			import models
from shared.rendering 	import PageRenderData


_logger = logging.getLogger(__name__)

# Я решил не думать над динамическими view, так как на
# сайте всего 3 страницы и я уже не успеваю по дедлайну.

# А так я бы развил эту тему до динамических view и реализовал бы PageView

class BasePageView(View):
	_file_folder: str = 'content'
	_file_name: str | None = None

	def __init_subclass__(cls):
		if cls is BasePageView:
			raise TypeError('Не создавайте экземпляров базового класса!')

		if not cls._file_name:
			raise TypeError('_file_name должен быть задан!')

		if cls._file_name.endswith('.html'):
			raise ValueError('Название необходимо указывать без расширения .html')


	# @classmethod с @property помечен как deprecated API, нельзя совместить.
	# @property (или cached_property как у нас) тут необходимо для того, чтобы
	# поле нельзя было изменить.
	@cached_property
	def _template_name(self) -> str:
		# Django сам разрешит путь для всех ОС
		return f"{self._file_folder}/{self._file_name}.html"

	@classmethod
	def _get_page_render_data(cls):
		return PageRenderData(
			page = models.Page.objects.get(file_name = cls._file_name)
		)

	def get(self, request: HttpRequest):
		data = self._get_page_render_data()
		return render(request, self._template_name, {'data': data})


class MainPageView(BasePageView):
	_file_name = 'index'

	def get(self, request: HttpRequest):
		data = self._get_page_render_data()
		form = ApplicationForm()

		return render(request, self._template_name, {'data': data, 'form': form})

	def post(self, request: HttpRequest):
		form = ApplicationForm(request.POST)

		if form.is_valid():
			form.save()
			return redirect('success')

		data = self._get_page_render_data()
		return render(request, self._template_name, {'data': data, 'form': form}, status = 400)


class SuccessPageView(BasePageView):
	_file_name = 'success'

class LegalPageView(BasePageView):
	_file_name = 'legal'
