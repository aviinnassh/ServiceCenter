# Vehicle Service Center Management System

A comprehensive Django-based web application designed to manage and streamline the operations of a vehicle service center. 

## Features

* **Customer Dashboard:** Allows customers to book services, view their service history, and check the status of their vehicles.
* **Service Center Dashboard:** Enables service center staff to manage bookings, assign jobs, update service statuses, and view pending tasks.
* **Service History Tracking:** Automatically records and maintains a detailed history of all services performed on a vehicle.
* **Invoice Generation:** Creates detailed invoices for completed services.

## Technologies Used

* **Backend:** Python, Django
* **Database:** SQLite (Development)
* **Frontend:** HTML, CSS

## Setup and Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aviinnassh/ServiceCenter.git
   cd ServiceCenter
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Make sure you have Django installed)*

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the application:**
   Open your browser and navigate to `http://127.0.0.1:8000/`.
