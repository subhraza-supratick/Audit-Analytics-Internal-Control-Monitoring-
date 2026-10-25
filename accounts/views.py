from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages

def switch_role(request):
    if request.method == 'POST':
        new_role = request.POST.get('role')
        valid_roles = ['ADMIN', 'AUDITOR', 'ANALYST', 'VIEWER']
        if new_role in valid_roles:
            request.session['active_role'] = new_role
            messages.success(request, f"Security context successfully switched to {new_role} role.")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'role': new_role})
        else:
            messages.error(request, f"Invalid role '{new_role}'. Permitted roles: {', '.join(valid_roles)}.")
        redirect_url = request.META.get('HTTP_REFERER', '/')
        return redirect(redirect_url)
    return redirect('/')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        if username:
            request.session['active_role'] = 'ADMIN'
            messages.success(request, f"Auditor '{username}' authenticated successfully. Access granted.")
            return redirect('dashboard_overview')
        else:
            messages.error(request, "Please enter your auditor username to sign in.")
    return render(request, 'accounts/login.html')
