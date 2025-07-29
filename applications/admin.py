import logging
from os import getenv

from django.contrib.admin	import StackedInline, ModelAdmin, action
from django.http 			import HttpResponse
from django.utils 			import timezone

from rangefilter.filters import DateRangeFilter

from applications.apps 		import ApplicationsConfig
from applications 			import models
from shared.admin.exporting import export_to_excel
from shared.admin 			import AdminModelRegistrator, make_singleton_model_admin_class


registrator = AdminModelRegistrator(
	ApplicationsConfig.name,
	logger = logging.getLogger(__name__)
)


@action(description = 'Экспортировать выбранное в Exсel')
def export_selected_to_exel(modeladmin, request, queryset) -> HttpResponse:
	name = f"Экспорт заявок {timezone.now().strftime("%d.%m.%Y")}"

	return export_to_excel(
		queryset, name,
		fields = ('requestener_name', 'phone_number', 'settlement', 'date'),
	)

@registrator.set_for_model(models.Application)
class ApplicationAdmin(ModelAdmin):
	readonly_fields = ('date',)
	list_display = ('application', 'phone_number', 'settlement', 'date')
	list_max_show_all = 100
	list_filter = (
		('date', DateRangeFilter),
	)
	sortable_by = ('date', )
	ordering = ('-date', )
	actions = [export_selected_to_exel]

	def application(self, obj: models.Application) -> str:
		return obj.requestener_name
	application.short_description = "Заявка от"


@registrator.set_for_model(models.TelegramBot)
class TelegrammBotAdmin(ModelAdmin):
	readonly_fields = ('token_success', )
	list_display = ('__str__', 'token_success')

	def token_success(self, obj: models.TelegramBot) -> bool:
		return getenv(obj.token_env_variable_name) is not None
	token_success.short_description = "Токен найден"
	token_success.boolean = True

registrator.register()
