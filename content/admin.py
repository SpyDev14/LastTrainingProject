import logging

from django.contrib	import admin

from shared.admin 	import AdminModelRegistrator, make_singleton_model_admin_class
from content.apps 	import ContentConfig
from content 		import models

registrator = AdminModelRegistrator(
	ContentConfig.name,
	logger = logging.getLogger(__name__)
)

registrator.exclude_model(models.RecruitersBranche)
class RecruitersBranchesInline(admin.StackedInline):
	model = models.RecruitersBranche
	can_delete = True
	extra = 0

@registrator.set_for_model(models.RecruitersContacts)
class RecruitersContactsAdmin(make_singleton_model_admin_class(models.RecruitersContacts)):
	inlines = [RecruitersBranchesInline]


_make_payment_fieldset = lambda name, field_name: \
	(name, {'fields': (f'{field_name}_payment_title', f'{field_name}_payment')})

@registrator.set_for_model(models.Payments)
class PaymentsAdmin(make_singleton_model_admin_class(models.Payments)):
	fieldsets = (
		('', {'fields': ('total_first_year_payment', 'total_first_month_payment', 'month_payment')}),
		_make_payment_fieldset('Региональная выплата', 'regional'),
		_make_payment_fieldset('Выплата от города', 'city'),
		_make_payment_fieldset('Выплата от Мин.О', 'offensive_ministry'),
		_make_payment_fieldset('Дополнительная выплата от Мин.О', 'offensive_ministry_other'),
		_make_payment_fieldset('Дополнительная выплата', 'additional'),
	)

@registrator.set_for_model(models.Page)
class PageAdmin(admin.ModelAdmin):
	search_fields = ('name', )

registrator.register()
