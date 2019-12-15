from django.urls import path

from . import views

app_name = 'tinymix'
urlpatterns = [
    # ex: /tinymix/
    path('', views.IndexView.as_view(), name='index'),
    # ex: /tinymix/config/5
    path('config/<int:pk>/', views.DetailView.as_view(), name='config'),
    # ex: /tinymix/config_new
    path('config/new/', views.config_new, name='config/new'),
    # ex: /tinymix/control/5
    path('control/<int:control_id>/', views.control, name='control'),
    # ex: /tinymix/control/publish
    path('control/publish/<int:control_id>', views.control_publish, name='control/publish'),
    # ex: /tinymix/value/5
    path('value/<int:value_id>/', views.value, name='value'),
]
