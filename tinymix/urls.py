from django.urls import path

from . import views

app_name = 'tinymix'
urlpatterns = [
    # ex: /tinymix/
    path('', views.index, name='index'),
    # ex: /tinymix/config/5
    path('config/<int:config_id>/', views.config, name='config'),
    # ex: /tinymix/control/5
    path('control/<int:control_id>', views.control, name='control'),
    # ex: /tinymix/control_edit/5
    path('control_edit/<int:control_id>', views.control_edit, name='control_edit'),
    # ex: /tinymix/value/5
    path('value/<int:value_id>', views.value, name='value'),
]
