from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # Doctors
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("doctors/add/", views.doctor_add, name="doctor_add"),
    path("doctors/<int:pk>/edit/", views.doctor_edit, name="doctor_edit"),
    path("doctors/<int:pk>/delete/", views.doctor_delete, name="doctor_delete"),

    # Schedules
    path("schedules/", views.schedule_list, name="schedule_list"),
    path("schedules/update/", views.schedule_update, name="schedule_update"),

    # Patients
    path("patients/", views.patient_list, name="patient_list"),
    path("patients/add/", views.patient_add, name="patient_add"),
    path("patients/<int:pk>/edit/", views.patient_edit, name="patient_edit"),
    path("patients/<int:pk>/history/", views.patient_history, name="patient_history"),

    # Appointments
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/add/", views.appointment_add, name="appointment_add"),
    path("appointments/<int:pk>/edit/", views.appointment_edit, name="appointment_edit"),
    path("appointments/<int:pk>/status/<int:status>/", views.appointment_update_status, name="appointment_update_status"),

    # Medical Records
    path("medical-records/", views.medical_record_list, name="medical_record_list"),
    path("medical-records/add/", views.medical_record_add, name="medical_record_add"),
    path("medical-records/<int:pk>/edit/", views.medical_record_edit, name="medical_record_edit"),

    # Orders
    path("orders/", views.order_list, name="order_list"),
    path("orders/add/", views.order_add, name="order_add"),
    path("orders/<int:pk>/pay/", views.order_pay, name="order_pay"),
    path("orders/<int:pk>/delete/", views.order_delete, name="order_delete"),

    # Settings
    path("settings/", views.settings_index, name="settings_index"),
    path("settings/department/add/", views.department_add, name="department_add"),
    path("settings/department/<int:pk>/edit/", views.department_edit, name="department_edit"),
    path("settings/department/<int:pk>/delete/", views.department_delete, name="department_delete"),
    path("settings/password/", views.password_change, name="password_change"),
]
