from django.db import models

# Create your models here.

from django.db import models


class Config(models.Model):
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
    value_current = models.ForeignKey('Value', on_delete=models.CASCADE)

    def __str__(self):
        return "<" + str(self.control_id) + ": " + self.control_name + " current=" + str(self.value_current) + ">"


class Value(models.Model):
    parent = models.ForeignKey(Control, on_delete=models.CASCADE)
    value_name = models.CharField('value name', max_length=200)
    value_id = models.IntegerField('value id')

    def __str__(self):
        return "<" + str(self.value_id) + ": " + self.value_name + ">"
