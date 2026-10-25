from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from transactions.models import AuditException, AuditLog
from audit_engine.rules import run_all_audit_rules

def run_audit_view(request):
    if request.method == 'POST':
        summary = run_all_audit_rules()
        messages.success(request, f"Audit Rules Engine executed successfully! Flagged {summary['total_exceptions']} exceptions ({summary['high_critical_count']} High/Critical Risk).")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'summary': summary})
        return redirect('/dashboard/exceptions/')
    return redirect('/')

def update_exception_status(request, exception_id):
    if request.method == 'POST':
        exc = get_object_or_404(AuditException, pk=exception_id)
        old_status = exc.status
        old_assigned = exc.assigned_to
        
        new_status = request.POST.get('status', exc.status)
        valid_statuses = ['OPEN', 'UNDER_REVIEW', 'RESOLVED', 'FALSE_POSITIVE']
        if new_status not in valid_statuses:
            messages.error(request, f"Invalid exception status '{new_status}' provided.")
            return redirect(request.META.get('HTTP_REFERER', '/dashboard/exceptions/'))

        assigned_to = request.POST.get('assigned_to', exc.assigned_to)
        notes = request.POST.get('review_notes', exc.review_notes)

        exc.status = new_status
        exc.assigned_to = assigned_to
        exc.review_notes = notes
        exc.save()

        user_name = request.session.get('active_role', 'Auditor')
        AuditLog.objects.create(
            user=user_name,
            action=f"UPDATE_STATUS_{new_status}",
            entity=f"AuditException #{exc.exception_id}",
            old_value=f"Status: {old_status}, Assigned: {old_assigned}",
            new_value=f"Status: {new_status}, Assigned: {assigned_to}, Notes: {notes}"
        )

        messages.success(request, f"Audit Exception EXC-{exc.exception_id} updated to '{new_status}'.")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'new_status': new_status})
        return redirect(request.META.get('HTTP_REFERER', '/dashboard/exceptions/'))
    return redirect('/dashboard/exceptions/')
