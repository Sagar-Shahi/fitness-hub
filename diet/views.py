from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .forms import NutritionRecordForm
from .models import NutritionRecord


@login_required
def index(request):
    records = NutritionRecord.objects.filter(user=request.user).order_by('-date')
    return render(request, 'diet/index.html', {'records': records})


@login_required
def create_record(request):
    if request.method == 'POST':
        form = NutritionRecordForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.user = request.user
            rec.save()
            return redirect('diet')
    else:
        form = NutritionRecordForm()
    return render(request, 'diet/create.html', {'form': form})


@login_required
def edit_record(request, pk):
    rec = get_object_or_404(NutritionRecord, pk=pk, user=request.user)
    if request.method == 'POST':
        form = NutritionRecordForm(request.POST, instance=rec)
        if form.is_valid():
            form.save()
            return redirect('diet')
    else:
        form = NutritionRecordForm(instance=rec)
    return render(request, 'diet/edit.html', {'form': form, 'record': rec})


@login_required
def delete_record(request, pk):
    rec = get_object_or_404(NutritionRecord, pk=pk, user=request.user)
    if request.method == 'POST':
        rec.delete()
        return redirect('diet')
    return render(request, 'diet/delete_confirm.html', {'record': rec})
