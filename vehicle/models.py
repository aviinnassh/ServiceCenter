from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime

# ---------------------------
# 1. Service Center Model
# ---------------------------
class ServiceCenter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    address = models.TextField()
    phone = models.CharField(max_length=10)
    email = models.EmailField(unique=True)
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ---------------------------
# 2. Customer Model
# ---------------------------
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    address = models.TextField()
    phone = models.CharField(max_length=10)
    email = models.EmailField(unique=True)
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ---------------------------
# 3. Vehicle Model
# ---------------------------
class Vehicle(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_number = models.CharField(max_length=50, unique=True)
    model = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    year = models.IntegerField(
    validators=[
        MinValueValidator(1900),
        MaxValueValidator(datetime.date.today().year)
    ]
)
    fuel_type = models.CharField(max_length=50)
    registration_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle_number} - {self.model}"


# ---------------------------
# 4. Staff Model (Service Center Staff)
# ---------------------------
class Staff(models.Model):
    service_center = models.ForeignKey(ServiceCenter, on_delete=models.CASCADE, related_name='staff')
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    date_joined = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.role})"


# ---------------------------
# 5. Service Booking Model
# ---------------------------
class ServiceBooking(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    service_center = models.ForeignKey(ServiceCenter, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    scheduled_date = models.DateField()
    description = models.TextField()
    status_choices = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='Pending')

    def __str__(self):
        return f"Booking {self.id} - {self.vehicle.vehicle_number}"


# ---------------------------
# 6. Job Assignment Model
# ---------------------------
class JobAssignment(models.Model):
    booking = models.ForeignKey(ServiceBooking, on_delete=models.CASCADE, related_name='assignments')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    assigned_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Job for {self.booking.vehicle.vehicle_number} assigned to {self.staff.name}"


# ---------------------------
# 7. ServiceStatus (history) Model
#    — changed to allow multiple status entries per booking
# ---------------------------
class ServiceStatus(models.Model):
    booking = models.ForeignKey(ServiceBooking, on_delete=models.CASCADE, related_name='statuses')
    updated_on = models.DateTimeField(auto_now_add=True)
    current_status = models.CharField(max_length=50)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Status of {self.booking.vehicle.vehicle_number}: {self.current_status}"


# ---------------------------
# 8. Invoice Model
# ---------------------------
class Invoice(models.Model):
    booking = models.OneToOneField(ServiceBooking, on_delete=models.CASCADE)
    service_center = models.ForeignKey(ServiceCenter, on_delete=models.CASCADE)

    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    issue_date = models.DateField(auto_now_add=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[('Paid', 'Paid'), ('Unpaid', 'Unpaid')],
        default='Unpaid'
    )

    def save(self, *args, **kwargs):
        # Auto-calculate total
        self.total_amount = (
            (self.parts_cost or 0) +
            (self.labor_cost or 0) +
            (self.tax or 0)
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice #{self.id} - {self.booking.vehicle.vehicle_number}" 



# ---------------------------
# 9. Service History Model (fixed: add service_center)
# ---------------------------
class ServiceHistory(models.Model):
    booking = models.ForeignKey(ServiceBooking, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    service_center = models.ForeignKey(ServiceCenter, on_delete=models.CASCADE)
    service_date = models.DateField()
    details = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)


    def __str__(self):
        return f"History for {self.vehicle.vehicle_number}"


# ---------------------------
# 10. Reminder & Offers Model
# ---------------------------
class ReminderOffer(models.Model):
    service_center = models.ForeignKey(ServiceCenter, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    message = models.TextField()
    sent_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reminder: {self.title} to {self.customer.user.username}"
