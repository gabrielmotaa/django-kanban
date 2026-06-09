from django.shortcuts import render


def index(request):
    return render(request, "kanban/templates/index.html")
