def rbac_context(request):
    """Context processor providing RBAC role info to all Django templates."""
    active_role = getattr(request, 'active_role', 'AUDITOR')
    return {
        'ACTIVE_ROLE': active_role,
        'IS_ADMIN': getattr(request, 'is_admin', False),
        'IS_AUDITOR': getattr(request, 'is_auditor', False),
        'IS_ANALYST': getattr(request, 'is_analyst', False),
        'IS_VIEWER': getattr(request, 'is_viewer', True),
        'ROLE_CHOICES': [
            ('ADMIN', 'Admin'),
            ('AUDITOR', 'Auditor'),
            ('ANALYST', 'Analyst'),
            ('VIEWER', 'Viewer / Management'),
        ]
    }
