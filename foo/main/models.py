from django.db import models

class File(models.Model):
    file = models.FileField(upload_to='data/training')
    name = models.CharField(max_length = 20)
    desc = models.CharField(max_length = 100)
    attrList = models.CharField(max_length=1000)

    def __str__(self):
        return self.name