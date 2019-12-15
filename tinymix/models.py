from _socket import timeout

from django.db import models

# Create your models here.

from django.utils import timezone

from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.auth.keygen import keygen

from django.db import models


class ConfigManager(models.Manager):
    keygen("/tmp/adbkey")

    def create_config(self, name, device_id):
        config = self.create(name=name, device_id=device_id, created_date=timezone.now())

        try:
            with open('/tmp/adbkey') as f:
                priv = f.read()
            signer = PythonRSASigner('', priv)

            device = AdbDeviceTcp('192.168.1.148', 5555, default_timeout_s=1.)
            device.connect(rsa_keys=[signer], auth_timeout_s=10.5)

        except Exception as e:
            print("Destroying invalid config! " + str(e))
            config.delete()
            return e
        else:
            return config


class Config(models.Model):
    objects = ConfigManager()
    name = models.CharField(max_length=200)
    device_id = models.IntegerField('device id')
    created_date = models.DateTimeField('date created')

    def __str__(self):
        return "<" + self.name + " control_set=" + self.control_set.all().__str__() + ">"

    def was_created_recently(self):
        return self.created_date >= timezone.now() - datetime.timedelta(hours=1)


class Control(models.Model):
    config = models.ForeignKey(Config, on_delete=models.CASCADE)
    control_name = models.CharField('control name', max_length=200)
    control_id = models.IntegerField('control id')
    # note: instead of giving class name we "introspect"
    value_current = models.ForeignKey('Value', on_delete=models.CASCADE)

    def __str__(self):
        return "<" + str(self.control_id) + ": " + self.control_name + " current=" + str(self.value_current) + ">"


class Value(models.Model):
    parent = models.ForeignKey(Control, on_delete=models.CASCADE)
    value_name = models.CharField('value name', max_length=200)
    value_id = models.IntegerField('value id')

    def get_command(self):
        return "tinymix " + str(self.parent.control_id) + " " + str(self.value_id)

    def __str__(self):
        return "<" + str(self.value_id) + ": " + self.value_name + " @ " + str(self.parent.control_id) + ">"
