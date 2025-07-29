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
def make_base_page_view(file_name: str, file_folder: str = 'content'):
	class BasePageView(View):
		_file_name = file_name
		_file_path = f"{file_folder}/{file_name}.html"

		@classmethod
		def _get_page_render_data(cls):
			return PageRenderData(
				page = models.Page.objects.get(file_name = cls._file_name)
			)

		def get(self, request: HttpRequest):
			data = self._get_page_render_data()
			return render(request, self._file_path, {'data': data})

	return BasePageView

class MainPageView(make_base_page_view('index')):
	def get(self, request: HttpRequest):
		data = self._get_page_render_data()
		form = ApplicationForm()

		return render(request, self._file_path, {'data': data, 'form': form})

	def post(self, request: HttpRequest):
		form = ApplicationForm(request.POST)

		if form.is_valid():
			form.save()
			return redirect('success')

		data = self._get_page_render_data()
		return render(request, self._file_path, {'data': data, 'form': form}, status = 400)


class SuccessPageView(make_base_page_view('success')):
	pass

class LegalPageView(make_base_page_view('legal')):
	pass
