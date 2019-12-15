from django.urls import path

from . import views

urlpatterns = [
    # ex: /tinymix/
    path('', views.index, name='index'),
    # ex: /tinymix/5/
    path('<int:config_id>/', views.detail, name='detail'),
    # ex: /tinymix/5/results/
    path('<int:question_id>/values/', views.values, name='values'),
    # ex: /tinymix/5/vote/
    path('<int:question_id>/edit/', views.edit, name='edit'),
]
