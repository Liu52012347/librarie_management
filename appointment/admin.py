from django.contrib import admin
from .models import Department, Doctor, Schedule, Patient, Appointment, MedicalRecord, ChargeItem, Order

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "created_at"]

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "department", "title", "phone", "status", "created_at"]
    list_filter = ["department", "title", "status"]
    search_fields = ["name", "phone"]

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ["id", "doctor", "week_day", "start_time", "end_time", "max_patients", "is_off"]
    list_filter = ["week_day", "is_off"]

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "gender", "birthday", "phone", "created_at"]
    search_fields = ["name", "phone", "id_card"]

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "doctor", "appointment_date", "appointment_time", "status", "created_at"]
    list_filter = ["status", "appointment_date", "doctor"]
    search_fields = ["patient__name", "doctor__name"]

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ["id", "appointment", "created_at"]

@admin.register(ChargeItem)
class ChargeItemAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "category", "price"]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "appointment", "charge_item", "amount", "status", "paid_at", "created_at"]
    list_filter = ["status"]
