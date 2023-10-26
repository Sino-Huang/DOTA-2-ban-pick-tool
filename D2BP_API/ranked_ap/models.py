from django.db import models
from json import dumps
from hashlib import sha256

# Create your models here.

class Attribute(models.Model):
    name = models.CharField(max_length=32, primary_key=True)
    order = models.IntegerField()

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Attributes"
    
    def __str__(self):
        return self.name


class Hero(models.Model):
    name = models.CharField(max_length=32, primary_key=True)
    alt_name = models.CharField(max_length=32)
    primary_attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)

    class Meta:
        ordering = ['primary_attribute', 'name']
        verbose_name_plural = "Heroes"

    def __str__(self):
        return self.name

class GameVersion(models.Model):
    version = models.CharField(max_length=32, primary_key=True)
    hero_list = models.ManyToManyField(Hero, default=Hero.objects.all)

    def __str__(self):
        return self.version


class Query(models.Model):
    query_id = models.CharField(max_length=64, primary_key=True)
    version = models.ForeignKey(GameVersion, on_delete=models.CASCADE, default="7.34d")
    round = models.IntegerField()
    ban_list = models.ManyToManyField(Hero, related_name="ban_list")
    opponent_pick_list = models.ManyToManyField(Hero, related_name="opponent_pick_list")
    ally_pick_list = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', related_name='queries', on_delete=models.SET_NULL)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = "Queries"
    
    def __str__(self):
        return dumps({
            "query_id": self.query_id,
            "version": self.version.version,
            "round": self.round,
            "ban_list": sorted([hero.name for hero in self.ban_list.all()]),
            "opponent_pick_list": sorted([hero.name for hero in self.opponent_pick_list.all()]),
            "ally_pick_list": self.ally_pick_list,
        }, indent=4)

    def compute_query_id(self):
        # concatenate values
        values = f"{self.version.version}{self.round}"
        values += "".join(sorted(hero.name for hero in self.ban_list.all()))
        values += "".join(sorted(hero.name for hero in self.opponent_pick_list.all()))
        values += dumps(self.ally_pick_list, sort_keys=True)
        # compute SHA256 hash
        return sha256(values.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        self.query_id = self.compute_query_id()
        super(Query, self).save(*args, **kwargs)