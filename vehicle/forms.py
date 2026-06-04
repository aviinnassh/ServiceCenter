from django import forms
from django.contrib.auth.models import User
from datetime import date

from .models import (
    ServiceCenter, Customer, Vehicle, Staff,
    ServiceBooking, JobAssignment, ServiceStatus,
    Invoice, ServiceHistory, ReminderOffer
)

# ---------------------------
# 1. User Registration Forms
# ---------------------------
class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "address", "phone", "email"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2})}


class ServiceCenterForm(forms.ModelForm):
    class Meta:
        model = ServiceCenter
        fields = ["name", "address", "phone", "email"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2})}

# ---------------------------
# 2. Vehicle Form (customer field removed)
# ---------------------------
class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['vehicle_number', 'model', 'manufacturer', 'year', 'fuel_type']


# ---------------------------
# 3. Staff Form (service_center set server-side)
# ---------------------------
class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['name', 'role', 'phone', 'email']


# ---------------------------
# 4. Service Booking Form (customer set server-side, validate scheduled_date)
# ---------------------------
class ServiceBookingForm(forms.ModelForm):
    class Meta:
        model = ServiceBooking
        fields = ['vehicle', 'service_center', 'scheduled_date', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'customer'):
            self.fields['vehicle'].queryset = Vehicle.objects.filter(customer=user.customer)
        else:
            self.fields['vehicle'].queryset = Vehicle.objects.none()

    def clean_scheduled_date(self):
        sd = self.cleaned_data.get('scheduled_date')
        if sd and sd < date.today():
            raise forms.ValidationError("Scheduled date cannot be in the past.")
        return sd


# ---------------------------
# 5. Job Assignment Form
# ---------------------------
class JobAssignmentForm(forms.ModelForm):
    class Meta:
        model = JobAssignment
        fields = ['staff', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, booking=None, **kwargs):
        super().__init__(*args, **kwargs)
        if booking:
            # Only show staff of that booking’s service center
            self.fields['staff'].queryset = Staff.objects.filter(
                service_center=booking.service_center
            )
        else:
            self.fields['staff'].queryset = Staff.objects.none()


# ---------------------------
# 6. Service Status Form
# ---------------------------
class ServiceStatusForm(forms.ModelForm):
    class Meta:
        model = ServiceStatus
        fields = ['current_status', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }


# ---------------------------
# 7. Invoice Form
# ---------------------------
class InvoiceForm(forms.ModelForm):
    total_amount = forms.DecimalField(
        required=False,
        disabled=True,
        label="Total Amount"
    )

    class Meta:
        model = Invoice
        fields = ['labor_cost', 'parts_cost', 'tax']
        widgets = {
            'labor_cost': forms.NumberInput(attrs={'step': '0.01'}),
            'parts_cost': forms.NumberInput(attrs={'step': '0.01'}),
            'tax': forms.NumberInput(attrs={'step': '0.01'}),
        }



# ---------------------------
# 8. Service History Form
# ---------------------------
class ServiceHistoryForm(forms.ModelForm):
    class Meta:
        model = ServiceHistory
        fields = ['booking', 'service_date', 'details']
        widgets = {
            'service_date': forms.DateInput(attrs={'type': 'date'}),
            'details': forms.Textarea(attrs={'rows': 3}),
        }


# ---------------------------
# 9. Reminder / Offer Form
# ---------------------------
class ReminderOfferForm(forms.ModelForm):
    class Meta:
        model = ReminderOffer
        fields = ['title', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }
