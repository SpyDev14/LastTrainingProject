from django.urls 	import path
from content 		import views

urlpatterns = [
	path('', 		views.MainPageView.as_view(), 	name = 'main'),
	path('legal', 	views.LegalPageView.as_view(), 	name = 'legal'),
	path('success', views.SuccessPageView.as_view(),name = 'success'),
]
