# Create your models here.
from django.forms import forms
from django.utils import timezone

from django.db import models

from ppadb.client import Client as AdbClient
import re


class Adb:
    client = AdbClient(host="127.0.0.1", port=5037)
    device = None
    ip = "172.21.114.90"

    def get_device(new_ip):
        if Adb.ip != new_ip:
            if new_ip is not None:
                Adb.ip = new_ip
            elif Adb.device is not None:
                return Adb.device

            Adb.device = Adb.client.device(Adb.ip + ":5555")
            try:
                Adb.device.root()
            except Exception as e:
                pass
            else:
                return Adb.device
        elif Adb.device is None:
            Adb.device = Adb.client.device(Adb.ip + ":5555")
            return Adb.device
        else:
            return Adb.device


def fetch_controls(ip, device_id):
    # ('0', 'ENUM', '1', 'MIC Bias VCM Bandgap', 'High Performance')
    output = Adb.get_device(ip).shell("tinymix -D " + str(device_id))
    controls = re.compile(r"^([0-9]+)\W+([A-Z]+)\W+([0-9]+)\W+([\w ]+?)[ \t]{2,}(.*)$",
                          re.MULTILINE).findall(output)
    return controls


class ConfigManager(models.Manager):
    def dynamic_refresh(self, device_id, pk, ip=None):
        try:
            cfg = Config.objects.get(pk=pk)

            fetched_controls = fetch_controls(ip, device_id)
            for fresh in fetched_controls:
                control_id = fresh[0]
                control_value_name = fresh[4]
                try:
                    control_to_update = cfg.control_set.get(control_id=control_id)
                    control_to_update.value_readback = control_value_name
                    control_to_update.save()
                except Control.DoesNotExist as e:
                    pass

        except Exception as e:
            print("Dynamic refhres failed ")
            raise e
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

                # print("need Control: " + str(control_id) + " " + control_name)

                control = Control.objects.fetch_control(ip=ip,
                                                        config=config,
                                                        control_id=control_id,
                                                        control_name=control_name,
                                                        control_type=control_type,
                                                        control_size=control_size)

        except Exception as e:
            print("Destroying invalid config! " + str(e))
            config.delete()
            raise e
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
    def fetch_control(self, ip, config, control_id, control_name, control_type, control_size):

        def build_control():
            _config = config
            _control_id = control_id
            _control_name = control_name
            _control_type = control_type
            return self.create(config=_config, control_id=_control_id, control_name=_control_name,
                               control_type=_control_type, value_stored=None)

        output = Adb.get_device(ip).shell("tinymix " + control_id)

        if control_type == "BOOL":
            control = build_control()

            # LINEA Mixer IN5 Switch: Off
            match = re.compile(r"(.*?:)(.*)").match(output)
            value_name = match[2].strip(" ")

            switcher = {
                "Off": 0,
                "On": 1
            }

            for key in switcher:
                value = Value.objects.create_value(value_id=switcher[key],
                                                   enum_value_name=key,
                                                   parent_control=control)
                # print("bool key='" + key + "' value='" + value_name + "' name=" + control_name)
                if key == value_name:
                    control.store_value(value)

        elif control_type == "ENUM":
            control = build_control()

            # MIC Bias VCM Bandgap:   Low Power       >High Performance
            match = re.compile(r"(.*?:)(.*)").match(output)
            value_names = match[2]

            #    Low Power       >High Performance
            value_names = re.compile(r"(([\w.,:*-_]+[ ]?)+|([ >]?[\w.,:*-_]+)+)").findall(value_names)

            value_id = 0
            for name in value_names:
                value_name = name[0].strip(" ")
                current = False
                if value_name.startswith(">"):
                    current = True
                    value_name = value_name.strip(">")

                # print("need Value: " + str(value_id) + " '" + value_name + "' curr=" + str(current) + " for " + str(
                #     control))

                value = Value.objects.create_value(value_id=value_id,
                                                   enum_value_name=value_name,
                                                   parent_control=control)
                value_id = value_id + 1

                # if this was the current value for this control -- store the relationship
                if current:
                    control.store_value(value)

        elif control_type == "INT":
            control = build_control()

            # 54      INT     2       Receiver Volume                          21 21
            # LINEB Volume: 2 (range 0->5)
            match = re.compile(r"(.*?): ([\d+ ]*) \(range (.*)\)").match(output)
            value_name = match[1]
            values_current = match[2]
            values_range = match[3].split("->")

            print(value_name + " | " + str(values_current) + " | " + str(values_range) + " == " + str(control_size))

            value = Value.objects.create_int_value(int_value=values_current,
                                               values_number=control_size,
                                               int_value_min=values_range[0],
                                               int_value_max=values_range[1],
                                               parent_control=control)

            control.store_value(value)

            return control
        else:
            print("skipping " + control_type)
            return None


class Control(models.Model):
    objects = ControlManager()
    config = models.ForeignKey(Config, on_delete=models.CASCADE)
    control_type = models.CharField('type', max_length=20, default=None, null=True)
    control_name = models.CharField('control name', max_length=200)
    control_id = models.IntegerField('control id')
    # note: instead of giving class name we "introspect"
    value_stored = models.ForeignKey('Value', on_delete=models.CASCADE, null=True)
    value_readback = models.CharField('dynamic value', max_length=200, default=None, null=True)

    def __str__(self):
        return "<" + str(self.control_id) + ": " + self.control_name + " current=" + str(self.value_stored) + ">"

    def __init__(self, *args, **kwargs):
        super(Control, self).__init__(*args, **kwargs)
        # self.value_dynamic = None

    def store_value_by_label(self, label_name):
        if self.get_type() == "INT":
            value: Value = self.value_stored
            value.set_int(label_name)
            self.store_value(self.value_stored)
        else:
            value = self.value_set.get(enum_value_name=label_name)
            self.store_value(value)

    def store_value(self, value):
        self.value_stored = value
        self.save()

    def get_stored(self):
        return self.value_stored

    def get_type(self):
        return self.control_type

    def get_label(self):
        # return self.control_name + " " + (self.value_current.enum_value_name if self.value_current is not None else "None")
        return self.control_name

    def get_label_stored(self):
        return self.value_stored.get_label()

    def get_label_readback(self):
        if (self.value_readback is None) or (self.value_readback == self.get_label_stored()):
            return "="
        else:
            return str(self.value_readback)

    def apply_and_save(self, value, ip=None):
        self.apply(value, ip)
        self.store_value(value)

    def apply_stored(self, ip=None):
        self.value_stored.apply(ip)
        self.value_readback = self.value_stored.get_label()

    def apply(self, value, ip=None):
        value.apply(ip)
        self.value_readback = value.get_label()


class ValueManager(models.Manager):
    def create_value(self, value_id, enum_value_name, parent_control, values_type="ENUM"):
        value = self.create(value_id=value_id, enum_value_name=enum_value_name, parent=parent_control, values_type=values_type)
        return value

    def create_int_value(self, int_value, int_value_min, int_value_max, parent_control, values_number):
        value = self.create(int_value=int_value, int_value_min=int_value_min, int_value_max=int_value_max, parent=parent_control, values_type="INT", values_number=values_number)
        return value


class Value(models.Model):
    objects = ValueManager()
    parent = models.ForeignKey(Control, on_delete=models.CASCADE)

    values_type = models.CharField('value name', max_length=20, default="ENUM")
    values_number = models.IntegerField('values number', default=1)

    enum_value_name = models.CharField('value name', max_length=200)
    value_id = models.IntegerField('value id', default=-1)

    int_value = models.CharField('value name', max_length=200, default="")
    int_value_min = models.IntegerField('int value min', default=-1)
    int_value_max = models.IntegerField('int value max', default=-1)

    def get_label(self):
        if self.values_type == "INT":
            return self.int_value
        else:
            return self.enum_value_name

    def get_value(self):
        if self.values_type == "INT":
            return self.int_value
        else:
            return str(self.value_id)

    def set_int(self, label_name):
        assert len(label_name.split(" ")) == self.values_number
        self.int_value = label_name
        pass

    def get_command(self):
        return "tinymix " + str(self.parent.control_id) + " " + self.get_value()

    def __str__(self):
        return "<" + str(self.value_id) + ": " + self.enum_value_name + " @ " + str(self.parent.control_id) + ">"

    def apply(self, ip=None, device_id=0):
        try:
            Adb.get_device(ip).shell(self.get_command())
        except Exception as e:
            raise e.with_traceback()
        else:
            pass
        pass


