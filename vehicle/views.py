# vehicle/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.db import transaction
from functools import wraps

from .models import (
    ServiceCenter, Customer, Vehicle, Staff,
    ServiceBooking, JobAssignment, ServiceStatus,
    Invoice, ServiceHistory, ReminderOffer
)

from .forms import (
    UserRegisterForm, CustomerForm, ServiceCenterForm,
    VehicleForm, StaffForm, ServiceBookingForm,
    JobAssignmentForm, ServiceStatusForm, InvoiceForm,
    ServiceHistoryForm, ReminderOfferForm
)


# ------------------------------------------------------------
# HELPER DECORATOR — ONLY SERVICE CENTER USERS ALLOWED
# ------------------------------------------------------------
def require_servicecenter(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not hasattr(request.user, 'servicecenter'):
            messages.error(request, "Access denied.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped


# ------------------------------------------------------------
# 1. AUTHENTICATION VIEWS
# ------------------------------------------------------------
def home(request):
    return render(request, "home.html")


def register_customer(request):
    if request.method == "POST":
        user_form = UserRegisterForm(request.POST)
        customer_form = CustomerForm(request.POST)

        if user_form.is_valid() and customer_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data["password"])
            user.save()

            customer = customer_form.save(commit=False)
            customer.user = user
            customer.save()

            messages.success(request, "Customer account created successfully.")
            return redirect("login")

    else:
        user_form = UserRegisterForm()
        customer_form = CustomerForm()

    return render(request, "register_customer.html", {
        "user_form": user_form,
        "customer_form": customer_form,
    })


def register_servicecenter(request):
    if request.method == "POST":
        user_form = UserRegisterForm(request.POST)
        servicecenter_form = ServiceCenterForm(request.POST)

        if user_form.is_valid() and servicecenter_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data["password"])
            user.save()

            sc = servicecenter_form.save(commit=False)
            sc.user = user
            sc.save()

            messages.success(request, "Service Center registered successfully.")
            return redirect("login")

    else:
        user_form = UserRegisterForm()
        servicecenter_form = ServiceCenterForm()

    return render(request, "register_servicecenter.html", {
        "user_form": user_form,
        "servicecenter_form": servicecenter_form,
    })


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, f"Welcome {user.username}")

            if hasattr(user, "customer"):
                return redirect("customer_dashboard")
            elif hasattr(user, "servicecenter"):
                return redirect("servicecenter_dashboard")

        messages.error(request, "Invalid username or password")

    return render(request, "login.html")


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect("login")


# ------------------------------------------------------------
# 2. DASHBOARDS
# ------------------------------------------------------------
@login_required
def customer_dashboard(request):
    if not hasattr(request.user, "customer"):
        messages.error(request, "Access denied.")
        return redirect("home")

    customer = request.user.customer

    bookings = ServiceBooking.objects.filter(
        customer=customer
    ).order_by('-booking_date')

    vehicles = Vehicle.objects.filter(customer=customer)

    service_histories = ServiceHistory.objects.filter(
        customer=customer
    ).order_by('-service_date')

    return render(request, "customer_dashboard.html", {
        "customer": customer,
        "bookings": bookings,
        "vehicles": vehicles,
        "service_histories": service_histories,  # ✅ added
    })


@login_required
@require_servicecenter
def servicecenter_dashboard(request):
    sc = request.user.servicecenter

    bookings = ServiceBooking.objects.filter(service_center=sc).order_by('-booking_date')
    staff = Staff.objects.filter(service_center=sc)

    customers = Customer.objects.filter(servicebooking__service_center=sc).distinct()

    pending_jobs = ServiceBooking.objects.filter(
        service_center=sc,
        status="Pending"
    ).order_by("-booking_date")

    return render(request, "servicecenter_dashboard.html", {
        "service_center": sc,
        "bookings": bookings,
        "staff": staff,
        "customers": customers,
        "pending_jobs": pending_jobs,
    })


# ------------------------------------------------------------
# 3. VEHICLE MANAGEMENT
# ------------------------------------------------------------
@login_required
def add_vehicle(request):
    if not hasattr(request.user, 'customer'):
        messages.error(request, "Only customers can add vehicles.")
        return redirect("home")

    if request.method == "POST":
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.customer = request.user.customer
            vehicle.save()
            messages.success(request, "Vehicle added successfully.")
            return redirect("view_vehicle")

    else:
        form = VehicleForm()

    return render(request, "vehicle_form.html", {"form": form})


@login_required
def edit_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, customer=request.user.customer)

    if request.method == "POST":
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle updated successfully.")
            return redirect("view_vehicle")

    else:
        form = VehicleForm(instance=vehicle)

    return render(request, "edit_vehicle.html", {"form": form})


@login_required
def delete_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, customer=request.user.customer)
    vehicle.delete()
    messages.success(request, "Vehicle deleted.")
    return redirect("view_vehicle")


@login_required
def view_vehicle(request):
    if not hasattr(request.user, 'customer'):
        messages.error(request, "Access denied.")
        return redirect("home")

    vehicles = Vehicle.objects.filter(customer=request.user.customer)
    return render(request, "vehicle_list.html", {"vehicles": vehicles})


# ------------------------------------------------------------
# 4. SERVICE BOOKING
# ------------------------------------------------------------
@login_required
def booking_service(request):
    if not hasattr(request.user, 'customer'):
        messages.error(request, "Only customers can book services.")
        return redirect("home")

    if request.method == "POST":
        form = ServiceBookingForm(request.POST, user=request.user)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user.customer
            booking.status = "Pending"
            booking.save()

            messages.success(request, "Service booked successfully.")
            return redirect("view_bookings")

    else:
        form = ServiceBookingForm(user=request.user)

    return render(request, "booking_service.html", {"form": form})


@login_required
def view_bookings(request):

    if hasattr(request.user, "customer"):
        bookings = ServiceBooking.objects.filter(customer=request.user.customer)

    elif hasattr(request.user, "servicecenter"):
        bookings = ServiceBooking.objects.filter(service_center=request.user.servicecenter)

    else:
        bookings = []

    return render(request, "booking_list.html", {"bookings": bookings})


# ------------------------------------------------------------
# 5. SERVICE CENTER OPERATIONS
# ------------------------------------------------------------
@login_required
@require_servicecenter
def add_staff(request):
    if request.method == "POST":
        form = StaffForm(request.POST)
        if form.is_valid():
            staff = form.save(commit=False)
            staff.service_center = request.user.servicecenter
            staff.save()
            messages.success(request, "Staff added successfully.")
            return redirect("staff_list")

    else:
        form = StaffForm()

    return render(request, "staff_form.html", {"form": form})


@login_required
@require_servicecenter
def staff_list(request):
    staff = Staff.objects.filter(service_center=request.user.servicecenter)
    return render(request, "staff_list.html", {"staff": staff})


@login_required
@require_servicecenter
def edit_staff(request, id):
    staff = get_object_or_404(Staff, id=id, service_center=request.user.servicecenter)

    if request.method == "POST":
        form = StaffForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff updated successfully.")
            return redirect("staff_list")

    else:
        form = StaffForm(instance=staff)

    return render(request, "edit_staff.html", {"form": form})


@login_required
@require_servicecenter
def delete_staff(request, id):
    staff = get_object_or_404(Staff, id=id, service_center=request.user.servicecenter)
    staff.delete()
    messages.success(request, "Staff deleted.")
    return redirect("staff_list")


# ------------------------------------------------------------
# FIXED PENDING JOBS VIEW
# ------------------------------------------------------------
@login_required
@require_servicecenter
def pending_jobs(request):
    service_center = request.user.servicecenter

    pending = ServiceBooking.objects.filter(
        service_center=service_center,
        status="Pending"
    ).order_by("-booking_date")

    return render(request, "pending_jobs.html", {
        "pending_bookings": pending,
    })


# ------------------------------------------------------------
# 6. JOB ASSIGNMENT
# ------------------------------------------------------------
@login_required
@require_servicecenter
def assign_job(request, booking_id):
    booking = get_object_or_404(ServiceBooking, id=booking_id)
    booking.status = "In Progress"
    booking.save()
    

    if booking.service_center != request.user.servicecenter:
        return HttpResponseForbidden("Not your booking.")

    if request.method == "POST":
        form = JobAssignmentForm(request.POST, booking=booking)
        if form.is_valid():
            job = form.save(commit=False)
            job.booking = booking
            job.save()
            messages.success(request, "Job assigned successfully.")
            return redirect("assigned_jobs_view")

    else:
        form = JobAssignmentForm(booking=booking)

    return render(request, "assign_job.html", {
        "form": form,
        "booking": booking
    })



@login_required
@require_servicecenter
def assigned_jobs_view(request):
    service_center = request.user.servicecenter

    jobs = JobAssignment.objects.filter(
        booking__service_center=service_center
    ).select_related(
        "booking",
        "booking__customer",
        "booking__vehicle",
        "staff"
    ).order_by("-id")

    return render(request, "assigned_jobs_view.html", {
        "jobs": jobs
    })

# ------------------------------------------------------------
# 7. BOOKING STATUS UPDATE
# ------------------------------------------------------------
@login_required
@require_servicecenter
def update_booking_status(request, pk):
    booking = get_object_or_404(ServiceBooking, id=pk)

    if booking.service_center != request.user.servicecenter:
        return HttpResponseForbidden("Unauthorized")

    if request.method == "POST":
        form = ServiceStatusForm(request.POST)
        if form.is_valid():
            status_entry = form.save(commit=False)
            status_entry.booking = booking
            status_entry.save()

            # Update main booking status
            booking.status = status_entry.current_status
            booking.save()

            messages.success(request, "Booking status updated.")

            # ✅ FIX: pass booking.id
            return redirect("booking_status_view", booking_id=booking.id)

    else:
        form = ServiceStatusForm()

    return render(request, "update_status.html", {
        "form": form,
        "booking": booking
    })




@login_required
def booking_status_view(request, booking_id):
    booking = get_object_or_404(ServiceBooking, id=booking_id)

    # Authorization
    if hasattr(request.user, "customer"):
        if booking.customer != request.user.customer:
            return HttpResponseForbidden("Access denied.")
    elif hasattr(request.user, "servicecenter"):
        if booking.service_center != request.user.servicecenter:
            return HttpResponseForbidden("Access denied.")
    else:
        return HttpResponseForbidden("Unauthorized")

    status_updates = ServiceStatus.objects.filter(
        booking=booking
    ).order_by("-updated_on")  # ✅ FIXED

    return render(request, "booking_status_view.html", {
        "booking": booking,
        "status_updates": status_updates,
    })



@login_required
def view_bookings(request):
    # Check if logged-in user is a Service Center
    if hasattr(request.user, "servicecenter"):
        service_center = request.user.servicecenter
        
        # Get all bookings related to this service center
        bookings = ServiceBooking.objects.filter(
            service_center=service_center
        ).order_by("-scheduled_date")

    # If logged-in user is a Customer
    elif hasattr(request.user, "customer"):
        bookings = ServiceBooking.objects.filter(
            customer=request.user.customer
        ).order_by("-scheduled_date")

    else:
        return HttpResponseForbidden("You are not allowed to view this page.")

    context = {
        "bookings": bookings,
    }

    return render(request, "view_bookings.html", context)


@login_required
def manage_bookings(request):
    # Allow only service center users to access this page
    if not hasattr(request.user, "servicecenter"):
        return HttpResponseForbidden("Only service centers can view this page.")

    # Fetch all bookings linked to this service center
    bookings = ServiceBooking.objects.filter(
        service_center=request.user.servicecenter
    ).select_related(
        "customer", "vehicle"
    ).order_by("-id")

    context = {
        "bookings": bookings,
    }

    return render(request, "manage_bookings.html", context)


# ------------------------------------------------------------
# 8. INVOICE GENERATION
# ------------------------------------------------------------
@login_required
@require_servicecenter
def generate_invoice(request, booking_id):
    booking = get_object_or_404(ServiceBooking, id=booking_id)

    if booking.service_center != request.user.servicecenter:
        return HttpResponseForbidden("Unauthorized")

    if request.method == "POST":
        form = InvoiceForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                invoice = form.save(commit=False)
                invoice.booking = booking
                invoice.service_center = request.user.servicecenter
                invoice.save()

                # ✅ Update booking status
                booking.status = "Completed"
                booking.save()

                # ✅ CREATE SERVICE HISTORY
                ServiceHistory.objects.create(
                    booking=booking,
                    customer=booking.customer,
                    vehicle=booking.vehicle,
                    service_center=booking.service_center,
                    service_date=booking.scheduled_date,
                    details="Service completed successfully",
                    cost=invoice.total_amount
                )

            messages.success(request, "Invoice generated & service history saved.")
            return redirect("servicecenter_dashboard")

    else:
        form = InvoiceForm()

    return render(request, "invoice.html", {
        "form": form,
        "booking": booking
    })


@login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    return render(request, "invoice_detail.html", {
        "invoice": invoice
    })


# ------------------------------------------------------------
# 9. SERVICE HISTORY
# ------------------------------------------------------------



@login_required
def service_history(request):
    if not hasattr(request.user, "customer"):
        messages.error(request, "Access denied.")
        return redirect("home")

    histories = ServiceHistory.objects.filter(
        customer=request.user.customer
    ).select_related(
        "vehicle", "service_center", "booking"
    ).order_by("-service_date")

    return render(request, "service_history.html", {
        "histories": histories
    })



@login_required
def history_detail(request, history_id):
    # Only allow the logged-in customer to view their own history
    if not hasattr(request.user, "customer"):
        messages.error(request, "Access denied.")
        return redirect("home")

    history = get_object_or_404(
        ServiceHistory,
        id=history_id,
        customer=request.user.customer
    )

    return render(request, "history_detail.html", {
        "history": history
    })



