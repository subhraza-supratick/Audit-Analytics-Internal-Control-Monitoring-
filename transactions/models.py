from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    department_id = models.CharField(max_length=20, primary_key=True)
    department_name = models.CharField(max_length=100)
    cost_center = models.CharField(max_length=50)
    manager_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.department_name} ({self.cost_center})"

class Employee(models.Model):
    employee_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees')
    designation = models.CharField(max_length=100)
    region = models.CharField(max_length=50)
    manager_id = models.CharField(max_length=20, blank=True, null=True)
    joining_date = models.DateField()
    approval_limit = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
    bank_account = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, default='ACTIVE')

    def __str__(self):
        return f"{self.name} - {self.designation}"

class Vendor(models.Model):
    RISK_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    vendor_id = models.CharField(max_length=20, primary_key=True)
    vendor_name = models.CharField(max_length=150)
    vendor_type = models.CharField(max_length=50)
    region = models.CharField(max_length=50)
    bank_account = models.CharField(max_length=50)
    address = models.CharField(max_length=255, blank=True, null=True)
    registration_date = models.DateField()
    risk_category = models.CharField(max_length=20, choices=RISK_CHOICES, default='LOW')
    status = models.CharField(max_length=20, default='ACTIVE')

    def __str__(self):
        return f"{self.vendor_name} ({self.vendor_id})"

class PurchaseOrder(models.Model):
    po_id = models.CharField(max_length=30, primary_key=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='purchase_orders')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    po_date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    approval_status = models.CharField(max_length=20, default='APPROVED')
    approved_by = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.po_id} - ₹{self.amount:,.2f}"

class Invoice(models.Model):
    invoice_id = models.CharField(max_length=30, primary_key=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='invoices')
    po = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    invoice_date = models.DateField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, default='PENDING')
    reference_no = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.invoice_id} - ₹{self.amount:,.2f}"

class Payment(models.Model):
    payment_id = models.CharField(max_length=30, primary_key=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='WIRE_TRANSFER')
    bank_account = models.CharField(max_length=50)
    processed_by = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.payment_id} - ₹{self.amount:,.2f}"

class EmployeeExpense(models.Model):
    expense_id = models.CharField(max_length=30, primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='expenses')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    expense_date = models.DateField()
    category = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    approval_status = models.CharField(max_length=20, default='APPROVED')
    approved_by = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.expense_id} - ₹{self.amount:,.2f}"

class AuditException(models.Model):
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('UNDER_REVIEW', 'Under Review'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive'),
    ]
    exception_id = models.AutoField(primary_key=True)
    transaction_id = models.CharField(max_length=50)
    transaction_type = models.CharField(max_length=50, default='INVOICE') # INVOICE, PAYMENT, PO, EXPENSE
    exception_type = models.CharField(max_length=100) # Duplicate Invoice, Split Purchase, etc.
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    risk_score = models.IntegerField(default=50) # 0-100 score
    ml_anomaly_score = models.FloatField(default=0.0)
    description = models.TextField()
    detected_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='OPEN')
    assigned_to = models.CharField(max_length=100, default='Unassigned')
    review_notes = models.TextField(blank=True, null=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)

    def __str__(self):
        return f"EXC-{self.exception_id}: {self.exception_type} (Score: {self.risk_score})"

class AuditLog(models.Model):
    user = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    entity = models.CharField(max_length=100)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.user} - {self.action} on {self.entity}"
