from django.db import models

class Attribute(models.Model):
    name = models.CharField(primary_key=True, max_length=255)
    order = models.IntegerField()
    image = models.ImageField(upload_to='attribute_images', blank=True)

    class Meta:
        ordering = ('order',)
        verbose_name_plural = 'Attributes'
    
    def __str__(self):
        return self.name

class Hero(models.Model):
    name = models.CharField(max_length=100)
    alt_name = models.CharField(max_length=100)
    primary_attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='hero_images', blank=True)

    class Meta:
        ordering = ('primary_attribute', 'name',)
        verbose_name_plural = 'Heroes'
    
    def __str__(self):
        return self.name