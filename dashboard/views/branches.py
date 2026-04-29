from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext as _
from core.models import Branch
from dashboard.forms.branch_forms import BranchForm


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser, login_url='/dashboard/login/')(view_func)


@login_required
@superuser_required
def dashboard_branches(request):
    branches = Branch.objects.all().order_by('sort_order', 'name')
    context = {
        'branches': branches,
        'page_title': _('إدارة الفروع'),
        'current_page': _('إدارة الفروع'),
    }
    return render(request, 'dashboard/branches/branch_list.html', context)


@login_required
@superuser_required
def dashboard_branch_create(request):
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم إضافة الفرع بنجاح'))
            return redirect('dashboard:dashboard_branches')
    else:
        form = BranchForm()

    context = {
        'form': form,
        'page_title': _('إضافة فرع جديد'),
        'current_page': _('إضافة فرع جديد'),
    }
    return render(request, 'dashboard/branches/branch_form.html', context)


@login_required
@superuser_required
def dashboard_branch_edit(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            messages.success(request, _('تم تحديث الفرع بنجاح'))
            return redirect('dashboard:dashboard_branches')
    else:
        form = BranchForm(instance=branch)

    context = {
        'form': form,
        'branch': branch,
        'page_title': _('تعديل الفرع'),
        'current_page': _('تعديل الفرع'),
    }
    return render(request, 'dashboard/branches/branch_form.html', context)


@login_required
@superuser_required
def dashboard_branch_delete(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        branch.delete()
        messages.success(request, _('تم حذف الفرع بنجاح'))
        return redirect('dashboard:dashboard_branches')

    context = {
        'branch': branch,
        'page_title': _('حذف الفرع'),
        'current_page': _('حذف الفرع'),
    }
    return render(request, 'dashboard/branches/branch_confirm_delete.html', context)
