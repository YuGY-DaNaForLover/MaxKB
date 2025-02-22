from django.urls import path

from . import views

app_name = "wsd_ai_api"
urlpatterns = [
    path('wsd_ai_api/dataset/create', views.Dataset.Create.as_view()),
    path('wsd_ai_api/dataset/<str:dataset_id>/re_embedding', views.Dataset.ReEmbedding.as_view()),
    path('wsd_ai_api/dataset/<str:dataset_id>/re_sync', views.Dataset.ReSync.as_view()),
    path('wsd_ai_api/application/create', views.Application.CreateAndReturnUrl.as_view()),
    path('wsd_ai_api/application/<str:app_subject_identifier>/<str:qa_subject_identifier>', views.Application.ReturnUrl.as_view())
]
