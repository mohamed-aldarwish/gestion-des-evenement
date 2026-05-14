from django.db import models
from django.db import models
from events.models import Event

class Statistic(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE)
    nombre_inscrits = models.IntegerField(default=0)
    taux_remplissage = models.FloatField(default=0)

    def __str__(self):
        return f"Stats - {self.event.title}"
