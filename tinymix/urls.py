from django.urls import path

from . import views

urlpatterns = [
    # ex: /tinymix/
    path('', views.index, name='index'),
    # ex: /tinymix/5/
    path('config/<int:config_id>/', views.detail, name='detail'),
    # ex: /tinymix/5/results/
    path('control/<int:control_id>', views.control, name='control'),
    # ex: /tinymix/5/vote/
    path('edit/<int:value_id>', views.edit, name='edit'),
]
