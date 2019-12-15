from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.urls import reverse

from tinymix.models import Config, Control, Value


def index(request):
    latest_configs_list = Config.objects.order_by('-created_date')[:5]
    context = {
        'latest_configs_list': latest_configs_list,
    }
    return render(request, 'tinymix/index.html', context)


def config(request, config_id):
    config = get_object_or_404(Config, pk=config_id)
    return render(request, 'tinymix/config.html', {'config': config})


def control(request, control_id):
    # response = "You're looking at control %s."
    # return HttpResponse(response % control_id)
    c = get_object_or_404(Control, pk=control_id)
    return render(request, 'tinymix/control.html', {'control': c})


def control_edit(request, control_id):
    ctrl = get_object_or_404(Control, pk=control_id)
    try:
        val = ctrl.value_set.get(pk=request.POST['newvalue'])
    except (KeyError, Value.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'tinymix/control.html', {
            'control': ctrl,
            'error_message': "You didn't select a value.",
        })
    else:
        ctrl.value_current = val
        ctrl.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('tinymix:config', args=(ctrl.config.pk,)))
        # return render(request, 'tinymix/control_edit.html', {'value': val})


def value(request, value_id):
    v = get_object_or_404(Value, pk=value_id)
    return render(request, 'tinymix/value.html', {'value': v})
