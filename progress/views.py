from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .forms import ProgressRecordForm
from .models import ProgressRecord


@login_required
def index(request):
    records = ProgressRecord.objects.filter(user=request.user).order_by('-date')
    return render(request, 'progress/index.html', {'records': records})


@login_required
def create_record(request):
    if request.method == 'POST':
        form = ProgressRecordForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.user = request.user
            rec.save()
            return redirect('progress')
    else:
        form = ProgressRecordForm()
    return render(request, 'progress/create.html', {'form': form})


@login_required
def edit_record(request, pk):
    rec = get_object_or_404(ProgressRecord, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ProgressRecordForm(request.POST, instance=rec)
        if form.is_valid():
            form.save()
            return redirect('progress')
    else:
        form = ProgressRecordForm(instance=rec)
    return render(request, 'progress/edit.html', {'form': form, 'record': rec})


@login_required
def delete_record(request, pk):
    rec = get_object_or_404(ProgressRecord, pk=pk, user=request.user)
    if request.method == 'POST':
        rec.delete()
        return redirect('progress')
    return render(request, 'progress/delete_confirm.html', {'record': rec})
