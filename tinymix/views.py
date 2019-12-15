from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.template import loader

from tinymix.models import Config


def index(request):
    latest_configs_list = Config.objects.order_by('-created_date')[:5]
    context = {
        'latest_configs_list': latest_configs_list,
    }
    return render(request, 'tinymix/index.html', context)

def detail(request, config_id):
    config = get_object_or_404(Config, pk=config_id)
    return render(request, 'tinymix/detail.html', {'config': config})

def values(request, control_index):
    response = "You're looking at the values of control %s."
    return HttpResponse(response % control_index)

def edit(request, control_index):
    return HttpResponse("You're editing control %s." % control_index)