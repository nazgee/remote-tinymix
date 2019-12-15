from django.db import models

# Create your models here.

from django.db import models


class Config(models.Model):
    name = models.CharField(max_length=200)
    created_date = models.DateTimeField('date created')

    def __str__(self):
        return "<" + self.name + " control_set=" + self.control_set.all().__str__() + ">"

    def was_created_recently(self):
        return self.created_date >= timezone.now() - datetime.timedelta(hours=1)


class Control(models.Model):
    config = models.ForeignKey(Config, on_delete=models.CASCADE)
    control_name = models.CharField('control name', max_length=200)
    control_index = models.IntegerField('control index')
    value_current = models.ForeignKey('Value', on_delete=models.CASCADE)

    def __str__(self):
        return "<" + str(self.control_index) + ": " + self.control_name + " current=" + str(self.value_current) + ">"


class Value(models.Model):
    parent = models.ForeignKey(Control, on_delete=models.CASCADE)
    value_name = models.CharField('value name', max_length=200)
    value_index = models.IntegerField('value index')

    def __str__(self):
        return "<" + str(self.value_index) + ": " + self.value_name + ">"
