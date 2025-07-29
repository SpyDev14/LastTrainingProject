from django.apps import AppConfig
from dotenv import load_dotenv

load_dotenv()

class ApplicationsConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'applications'
	verbose_name = 'Заявки'

	def ready(self):
		import applications.signals
