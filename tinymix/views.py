from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.template import loader

from tinymix.models import Config, Control, Value


def index(request):
    latest_configs_list = Config.objects.order_by('-created_date')[:5]
    context = {
        'latest_configs_list': latest_configs_list,
    }
    return render(request, 'tinymix/index.html', context)


def detail(request, config_id):
    config = get_object_or_404(Config, pk=config_id)
    return render(request, 'tinymix/detail.html', {'config': config})


def control(request, control_id):
    # response = "You're looking at control %s."
    # return HttpResponse(response % control_id)
    control = get_object_or_404(Control, pk=control_id)
    return render(request, 'tinymix/control.html', {'control': control})


def edit(request, value_id):
    value = get_object_or_404(Value, pk=value_id)
    return render(request, 'tinymix/value.html', {'value': value})
