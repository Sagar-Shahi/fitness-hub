from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    # Minimal dashboard view to be expanded later
    return render(request, 'dashboard/index.html')
