from django.db import models

class Hero(models.Model):
    name = models.CharField(max_length=100)
    alt_name = models.CharField(max_length=100)
    main_attribute = models.CharField(max_length=100)
    image = models.ImageField(upload_to='hero_images', blank=True)

    class Meta:
        ordering = ('main_attribute', 'name',)
        verbose_name_plural = 'Heroes'
    
    def __str__(self):
        return self.name