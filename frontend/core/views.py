from django.shortcuts import render

from core.models import Attribute, Hero

def index(request):
    return render(request, 'core/index.html')

def hero_grid(request):
    attributes = Attribute.objects.all()
    heroes_by_attribute = {}
    for attribute in attributes:
        heroes_by_attribute[attribute] = Hero.objects.filter(primary_attribute=attribute)
    print(heroes_by_attribute)
    return render(request, 'core/hero_grid.html', {
        'attributes': attributes,
        'heroes_by_attribute': heroes_by_attribute,
    })