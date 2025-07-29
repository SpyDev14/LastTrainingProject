from django.db import models
from django.conf import settings

from ordered_model.models import OrderedModel
from solo.models          import SingletonModel
from tinymce.models       import HTMLField

from shared.rendering import render_data


# MARK: Singletones
_HTML_ADDITION_HELP_TEXT = "Этот текст будет добавлен в указанный тег в каждой html разметке на сайте"

@render_data.register_model_for_page_render_data
class SiteSettings(SingletonModel):
	site_favicon       = models.ImageField(blank = True, verbose_name = "Favicon сайта", upload_to = settings.MEDIA_ROOT / "icons")
	site_video         = models.FileField(blank = True, verbose_name = "Видео", upload_to = settings.MEDIA_ROOT / "videos")
	robots_txt_content = models.TextField(blank = True, verbose_name = "Содержимое Robots.txt")
	html_head_addition = models.TextField(blank = True, verbose_name = "Добавить в <head>", help_text = _HTML_ADDITION_HELP_TEXT)
	html_body_addition = models.TextField(blank = True, verbose_name = "Добавить в <body>", help_text = _HTML_ADDITION_HELP_TEXT)

	class Meta:
		verbose_name = "Настройки сайта"
		verbose_name_plural = "Настройки сайта"
	def __str__(self):
		return "Настройки сайта"

_contact_url_field = lambda vb_name: models.URLField(verbose_name = vb_name, blank = True)
@render_data.register_model_for_page_render_data
class RecruitersContacts(SingletonModel):
	tg_contact_link = _contact_url_field("Telegram")
	vk_contact_link = _contact_url_field("Вконтакте")
	dzen_contact_link = _contact_url_field("Дзен")
	classmates_contact_link = _contact_url_field("Одноклассники")

	class Meta:
		verbose_name = "Контакты вербовщиков"
		verbose_name_plural = "Контакты вербовщиков"
	def __str__(self): return "Контакты вербовщиков"

_payment_title_field = lambda verb_name: models.CharField(verbose_name = verb_name, blank = True)
_money_field = lambda verb_name: models.CharField(verbose_name = verb_name, blank = True)
@render_data.register_model_for_page_render_data
class Payments(SingletonModel):
	total_first_year_payment = _money_field("Суммарная плата за первый год")
	total_first_month_payment = _money_field("Суммарная плата за первый месяц")
	month_payment = _money_field("Месячное довольствие")

	regional_payment_title = _payment_title_field("Описание выплаты от администрации области")
	regional_payment = _money_field("Сумма единовременной выплаты от А. области")

	city_payment_title = _payment_title_field("Описание выплаты от администрации города")
	city_payment = _money_field("Сумма единовременной выплаты от А. города")

	offensive_ministry_payment_title = _payment_title_field("Описание выплаты от Мин.О")
	offensive_ministry_payment = _money_field("Сумма единовременной выплаты от Мин.О")

	offensive_ministry_other_payment_title = _payment_title_field("Описание иной выплаты от Мин.О")
	offensive_ministry_other_payment = _money_field("Сумма иной выплаты от Мин.О")

	additional_payment_title = _money_field("Описание дополнительной выплаты")
	additional_payment = _money_field("Сумма дополнительной выплаты")

	class Meta:
		verbose_name = "Выплаты"
		verbose_name_plural = "Выплаты"
	def __str__(self): return "Выплаты"


# MARK: Standart models
# Очередь в админ-панели не работает, нужно настроить

@render_data.register_model_for_page_render_data
class FAQPoint(OrderedModel):
	question = models.CharField(verbose_name = "Вопрос", unique = True)
	answer = HTMLField(verbose_name = "Ответ")

	class Meta(OrderedModel.Meta):
		verbose_name = "FAQ пункт"
		verbose_name_plural = "FAQ пункты"

	def __str__(self):
		return self.question

@render_data.register_model_for_page_render_data
class RecruitersBranche(models.Model):
	addres = models.CharField(verbose_name = "Адрес")
	number_phone = models.CharField(verbose_name = "Телефон")
	coordinates = models.CharField(verbose_name = "Координаты", blank = True)

	_link_to_contacts_for_admin_model_inline_drawning = models.ForeignKey(RecruitersContacts, on_delete = models.CASCADE)

	class Meta:
		verbose_name = "Филлиал вербовщиков"
		verbose_name_plural = "Филлиалы вербовщиков"

	def __str__(self):
		return f"#{self.pk}"

@render_data.register_model_for_requirement_in_page_render_data_constructor
class Page(models.Model):
	file_name = models.CharField(verbose_name = "Название файла", help_text = "Без .html", unique = True)
	name = models.CharField(verbose_name = "Название")
	title = models.CharField(help_text = "Название вкладки в браузере")
	ceo_content = HTMLField(verbose_name = "CEO контент", blank = True)

	class Meta:
		verbose_name = "Страница"
		verbose_name_plural = "Страницы сайта"

	def __str__(self):
		return self.name
