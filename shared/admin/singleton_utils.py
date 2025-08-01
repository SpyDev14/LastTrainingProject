from django.contrib.admin 	import ModelAdmin
from solo.models 			import SingletonModel
from django.http 			import HttpResponseRedirect
from django.urls 			import reverse

def make_singleton_model_admin_class(model: SingletonModel):
	meta = model._meta

	# Ревлизованно через прямое создание type только ради кастомного названия
	admin_class = type(
		f"{model.__name__}Admin",
		(ModelAdmin, ),
		{
			"has_add_permission": lambda *args, **kwargs: False,
			"has_delete_permission": lambda *args, **kwargs: False,
			"changelist_view": lambda *args, **kwargs: HttpResponseRedirect( # Также создаёт модель, если её нет
				reverse(f"admin:{meta.app_label}_{meta.model_name}_change", args = [model.get_solo().pk])
			)
		}
	)

	return admin_class
