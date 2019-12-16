from _socket import timeout

from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.urls import reverse
from django.views import generic

from tinymix.models import Config, Control, Value, ConfigManager, Adb


class IndexView(generic.ListView):
    model = Config
    template_name = 'tinymix/index.html'
    context_object_name = 'latest_configs_list'


    def render(self, request, context: dict = {}):
        context[self.context_object_name] = self.get_queryset()
        return render(request, self.template_name, context)

    def get_queryset(self):
        """Return the last five published Configs."""
        return Config.objects.order_by('-created_date')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['ipaddr'] = Adb.ip
        return context


def config_new(request):
    cfg = Config.objects.create_config(ip=request.POST['ip'], name=request.POST['name'], device_id=0)

    if not isinstance(cfg, Config):
        print("foo")
        return IndexView().render(request, context={"error_message": "Config creation failed! " + str(cfg)})

    return HttpResponseRedirect(reverse('tinymix:index'))


class DetailView(generic.DetailView):
    model = Config
    template_name = 'tinymix/config.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context['ipaddr'] = Adb.ip
        return context


def config_reload(request, pk):
    ip = None
    try:
        ip = request.POST['ip']
    except:
        pass


    if "download" in request.POST:
        Config.objects.dynamic_refresh(device_id=0, pk=pk, ip=ip)
    elif "upload" in request.POST:
        cfg = Config.objects.get(pk=pk)
        for ctrl in cfg.control_set.all():
            ctrl.apply_stored(ip)
    elif "save" in request.POST:
        cfg = Config.objects.get(pk=pk)
        for ctrl in cfg.control_set.all():
            ctrl.store_value_by_label(ctrl.value_readback)
    else:
        raise RuntimeError("This should never happen: " + str(request.POST))


    return HttpResponseRedirect(reverse('tinymix:config', args=(pk,)))

# def config(request, config_id):
#     config = get_object_or_404(Config, pk=config_id)
#     return render(request, 'tinymix/config.html', {'config': config})


def control(request, control_id):
    # response = "You're looking at control %s."
    # return HttpResponse(response % control_id)
    c = get_object_or_404(Control, pk=control_id)
    return render(request, 'tinymix/control.html', {'control': c, 'ipaddr': Adb.ip})


def control_publish(request, control_id):
    ctrl = get_object_or_404(Control, pk=control_id)
    try:
        val = ctrl.value_set.get(pk=request.POST['value_pk'])
        ip = request.POST['ip']
    except (KeyError, Value.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'tinymix/control.html', {
            'control': ctrl,
            'error_message': "You didn't select a value.",
        })
    else:
        if "apply_and_save" in request.POST:
            ctrl.apply_and_save(val, ip)
        else:
            ctrl.apply(val, ip)
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        Config.objects.dynamic_refresh(device_id=0, pk=ctrl.config.pk)
        return HttpResponseRedirect(reverse('tinymix:config', args=(ctrl.config.pk,)))
        # return render(request, 'tinymix/control_edit.html', {'value': val})


def value(request, value_id):
    v = get_object_or_404(Value, pk=value_id)
    return render(request, 'tinymix/value.html', {'value': v})
