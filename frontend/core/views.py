from django.shortcuts import render

def index(request):
    return render(request, 'core/index.html')

def hero_grid(request):
    return render(request, 'core/hero_grid.html')