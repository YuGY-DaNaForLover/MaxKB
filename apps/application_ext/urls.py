from django.urls import path

from . import views

app_name = "application_ext"
urlpatterns = [
    path('ext/application', views.ApplicationExtView.as_view(),
         name="application_ext"),
    path('ext/application/import', views.ApplicationExtView.Import.as_view()),
    path('ext/application/profile', views.ApplicationExtView.Profile.as_view(),
         name='application_ext/profile'),
    path('ext/application/qa-text', views.ApplicationQaTextView.Operate.as_view(),
         name='application_ext/qa-text/operate'),
    path('ext/application/wsd-chat-info/<str:app_subject_identifier>',
         views.WsdChatInfoView.as_view(), name='application_ext/wsd-chat-info'),
    path('ext/application/save_as_template', views.ApplicationTemplateView.as_view(),
         name='application_ext/save_as_template'),
    path('ext/application/<str:application_id>',
         views.ApplicationExtView.Operate.as_view(), name='application_ext/operate'),
    path('ext/application/<str:application_id>/export',
         views.ApplicationExtView.Export.as_view()),
    path('ext/application/qa-text/<str:application_qa_text_id>',
         views.ApplicationQaTextView.Operate.as_view(), name='application_ext/qa-text/delete'),
]
