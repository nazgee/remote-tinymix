# Create your models here.
from django.forms import forms
from django.utils import timezone

from django.db import models

from ppadb.client import Client as AdbClient
import re


class Adb:
    client = AdbClient(host="127.0.0.1", port=5037)
    device = None
    ip = "192.168.1.147"

    def get_device(new_ip):
        if (new_ip is not None) and ((Adb.ip != new_ip) or (Adb.device is None)):
            Adb.ip = new_ip
            Adb.device = Adb.client.device(Adb.ip + ":5555")
            try:
                Adb.device.root()
            except:
                pass

            return Adb.device
        return Adb.device

def fetch_controls(ip, device_id):
    try:
        output = Adb.get_device(ip).shell("tinymix -D " + str(device_id))

        # max98091-audio
        mixer = re.compile("Mixer name: '(.*)'").match(output)[1]
        controls = re.compile(r"^([0-9]+)\W+([A-Z]+)\W+([0-9]+)\W+([\w ]+?)[ \t]{2,}(.*)$",
                              re.MULTILINE).findall(output)

        # ('0', 'ENUM', '1', 'MIC Bias VCM Bandgap', 'High Performance')
        return controls

    except Exception as e:
        return e


class ConfigManager(models.Manager):
    def dynamic_refresh(self, device_id, config_pk, ip=None):
        try:
            cfg = Config.objects.get(pk=config_pk)

            fetched_controls = fetch_controls(ip, device_id)
            for fresh in fetched_controls:
                control_id = fresh[0]
                control_value_name = fresh[4]
                try:
                    control_to_update = cfg.control_set.get(control_id=control_id)
                    control_to_update.value_dynamic = control_value_name
                    control_to_update.save()
                except Control.DoesNotExist as e:
                    pass

        except Exception as e:
            print("Dynamic refhres failed ")
            raise e.with_traceback()
        else:
            print("Dynamic refhreh ok")
            pass


    def create_config(self, ip, name, device_id):
        config = self.create(name=name, device_id=device_id, created_date=timezone.now())

        try:
            controls = fetch_controls(ip, device_id)

            for control in controls:
                # ('0', 'ENUM', '1', 'MIC Bias VCM Bandgap', 'High Performance')
                control_id = control[0]
                control_type = control[1]
                control_size = control[2]
                control_name = control[3]
                control_value_name = control[4]

                # print("need Control: " + str(control_id) + " " + control_name)

                control = Control.objects.fetch_control(ip=ip,
                                                        config=config,
                                                        control_id=control_id,
                                                        control_name=control_name,
                                                        control_type=control_type,
                                                        current_value_name=control_value_name)



        except Exception as e:
            print("Destroying invalid config! " + str(e))
            config.delete()
            raise e.with_traceback()
            return e
        else:
            print("Got config " + str(config))
            return config


class Config(models.Model):
    objects = ConfigManager()
    name = models.CharField(max_length=200)
    device_id = models.IntegerField('device id')
    created_date = models.DateTimeField('date created')

    def __str__(self):
        return "<" + str(self.id) + " " + self.name + " control_set=" + self.control_set.all().__str__() + ">"

    def was_created_recently(self):
        return self.created_date >= timezone.now() - datetime.timedelta(hours=1)


class ControlManager(models.Manager):
    def fetch_control(self, ip, config, control_id, control_name, control_type, current_value_name):
        if control_type == "BOOL":
            control = self.create(config=config,
                                  control_id=control_id,
                                  control_name=control_name,
                                  value_current=None)
            output = Adb.get_device(ip).shell("tinymix " + control_id)

            # LINEA Mixer IN5 Switch: Off
            match = re.compile(r"(.*?:)(.*)").match(output)
            control_name = match[1].strip(" ")
            control_current = match[2].strip(" ")

            switcher = {
                "Off": 0,
                "On": 1
            }

            for key in switcher:
                value = Value.objects.create_value(value_id=switcher[key],
                                                   value_name=key,
                                                   parent_control=control)
                print("bool key='" + key + "' value='" + control_current + "' name=" + control_name)
                if key == control_current:
                    control.value_current = value
                    control.save()

        elif control_type == "ENUM":
            control = self.create(config=config,
                                  control_id=control_id,
                                  control_name=control_name,
                                  value_current=None)
            output = Adb.get_device(ip).shell("tinymix " + control_id)

            # MIC Bias VCM Bandgap:   Low Power       >High Performance
            match = re.compile(r"(.*?:)(.*)").match(output)
            control_name = match[1]
            control_values = match[2]

            #    Low Power       >High Performance
            values = re.compile(r"(([\w.,:*-_]+[ ]?)+|([ >]?[\w.,:*-_]+)+)").findall(control_values)

            value_id = 0
            for value in values:
                value_name = value[0].strip(" ")
                current = False
                if value_name.startswith(">"):
                    current = True
                    value_name = value_name.strip(">")

                print("need Value: " + str(value_id) + " '" + value_name + "' curr=" + str(current) + " for " + str(
                    control))

                value = Value.objects.create_value(value_id=value_id,
                                                   value_name=value_name,
                                                   parent_control=control)
                value_id = value_id + 1

                # if this was the current value for this control -- store the relationship
                if current:
                    control.value_current = value
                    control.save()

            return control
        else:
            print("skipping " + control_type)
            return None


class Control(models.Model):
    objects = ControlManager()
    config = models.ForeignKey(Config, on_delete=models.CASCADE)
    control_name = models.CharField('control name', max_length=200)
    control_id = models.IntegerField('control id')
    # note: instead of giving class name we "introspect"
    value_current = models.ForeignKey('Value', on_delete=models.CASCADE, null=True)
    value_dynamic = models.CharField('dynamic value', max_length=200, default=None, null=True)

    def __str__(self):
        return "<" + str(self.control_id) + ": " + self.control_name + " current=" + str(self.value_current) + ">"

    def __init__(self, *args, **kwargs):
        super(Control, self).__init__(*args, **kwargs)
        # self.value_dynamic = None

    def get_label(self):
        # return self.control_name + " " + (self.value_current.value_name if self.value_current is not None else "None")
        return self.control_name

    def get_dynamic_state(self):
        # return self.control_name + " " + (self.value_current.value_name if self.value_current is not None else "None")
        if self.value_dynamic is None or (self.value_current.value_name == self.value_dynamic):
            return self.value_current.value_name
        else:
            return self.value_current.value_name + " --------> " + str(self.value_dynamic)

    def apply_and_save(self, value, ip=None):
        value.apply(ip)
        self.value_current = value
        self.save()

    def apply(self, value, ip=None):
        value.apply(ip)



class ValueManager(models.Manager):
    def create_value(self, value_id, value_name, parent_control):
        value = self.create(value_id=value_id, value_name=value_name, parent=parent_control)

        return value


class Value(models.Model):
    objects = ValueManager()
    parent = models.ForeignKey(Control, on_delete=models.CASCADE)
    value_name = models.CharField('value name', max_length=200)
    value_id = models.IntegerField('value id')

    def get_label(self):
        return self.value_name

    def get_command(self):
        return "tinymix " + str(self.parent.control_id) + " " + str(self.value_id)

    def __str__(self):
        return "<" + str(self.value_id) + ": " + self.value_name + " @ " + str(self.parent.control_id) + ">"

    def apply(self, ip, device_id=0):
        try:
            Adb.get_device(ip).shell("tinymix " + str(self.parent.control_id) + " " + str(self.value_id))
        except Exception as e:
            print("apply failed ")
            raise e.with_traceback()
        else:
            print("apply ok")
            pass
        pass
