import logging
from django.apps import AppConfig

_logger = logging.getLogger(__name__)

class ContentConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'content'
	verbose_name = 'Контент сайта'

	def ready(self):
		from shared.rendering import render_data
		render_data._init_page_render_data_class()
