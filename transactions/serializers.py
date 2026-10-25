from rest_framework import serializers
from transactions.models import Department, Employee, Vendor, PurchaseOrder, Invoice, Payment, EmployeeExpense, AuditException

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.department_name')
    class Meta:
        model = Employee
        fields = '__all__'

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'

class PurchaseOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.ReadOnlyField(source='vendor.vendor_name')
    employee_name = serializers.ReadOnlyField(source='employee.name')
    class Meta:
        model = PurchaseOrder
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    vendor_name = serializers.ReadOnlyField(source='vendor.vendor_name')
    class Meta:
        model = Invoice
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    vendor_name = serializers.ReadOnlyField(source='vendor.vendor_name')
    class Meta:
        model = Payment
        fields = '__all__'

class EmployeeExpenseSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source='employee.name')
    class Meta:
        model = EmployeeExpense
        fields = '__all__'

class AuditExceptionSerializer(serializers.ModelSerializer):
    vendor_name = serializers.ReadOnlyField(source='vendor.vendor_name')
    class Meta:
        model = AuditException
        fields = '__all__'
