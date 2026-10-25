class RBACSimulationMiddleware:
    """Middleware allowing session-based role switching for demonstration purposes."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_role = request.session.get('active_role', 'AUDITOR')
        request.active_role = current_role
        
        # Helper permission properties
        request.is_admin = (current_role == 'ADMIN')
        request.is_auditor = (current_role in ['ADMIN', 'AUDITOR'])
        request.is_analyst = (current_role in ['ADMIN', 'ANALYST'])
        request.is_viewer = True # Everyone can view read-only dashboards
        
        response = self.get_response(request)
        return response
