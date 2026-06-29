from django import forms
from .models import Doctor, Patient, Appointment, MedicalRecord, Order, ChargeItem, Schedule, Department
from django.utils import timezone

class LoginForm(forms.Form):
    username = forms.CharField(max_length=50, label="用户名", widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "请输入用户名"}))
    password = forms.CharField(max_length=50, label="密码", widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "请输入密码"}))

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ["name", "department", "title", "phone", "intro"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.Select(attrs={"class": "form-select"}),
            "title": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "intro": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["name", "gender", "birthday", "phone", "id_card", "address", "allergy_history"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "birthday": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "id_card": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "allergy_history": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "appointment_date", "appointment_time", "symptom", "remark"]
        widgets = {
            "patient": forms.Select(attrs={"class": "form-select"}),
            "doctor": forms.Select(attrs={"class": "form-select"}),
            "appointment_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "appointment_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "symptom": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "remark": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean_appointment_date(self):
        date = self.cleaned_data["appointment_date"]
        if date < timezone.localdate():
            raise forms.ValidationError("预约日期不能早于今天")
        return date

    def clean(self):
        cleaned = super().clean()
        doctor = cleaned.get("doctor")
        date = cleaned.get("appointment_date")
        time_val = cleaned.get("appointment_time")
        if doctor and date and time_val:
            week_day = date.weekday()
            # Monday is 0 in Python weekday, but our Schedule uses 0=Monday
            schedules = Schedule.objects.filter(doctor=doctor, week_day=week_day)
            if not schedules.exists():
                raise forms.ValidationError("该医生当天没有排班")
            sched = schedules.first()
            if sched.is_off:
                raise forms.ValidationError("该医生当天休息")
            if time_val < sched.start_time or time_val >= sched.end_time:
                raise forms.ValidationError(f"预约时间不在医生排班范围内 ({sched.start_time:%H:%M}-{sched.end_time:%H:%M})")
            # Check for duplicate time slot
            if Appointment.objects.filter(doctor=doctor, appointment_date=date, appointment_time=time_val).exclude(status__in=[4, 5]).exists():
                raise forms.ValidationError("该时段已被预约")
        return cleaned

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ["appointment", "diagnosis", "prescription", "notes"]
        widgets = {
            "appointment": forms.Select(attrs={"class": "form-select"}),
            "diagnosis": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "prescription": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["appointment", "charge_item", "amount", "status"]
        widgets = {
            "appointment": forms.Select(attrs={"class": "form-select"}),
            "charge_item": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

class ChargeItemForm(forms.ModelForm):
    class Meta:
        model = ChargeItem
        fields = ["name", "price", "category"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }

class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(max_length=50, label="原密码", widget=forms.PasswordInput(attrs={"class": "form-control"}))
    new_password = forms.CharField(max_length=50, label="新密码", widget=forms.PasswordInput(attrs={"class": "form-control"}))
    confirm_password = forms.CharField(max_length=50, label="确认新密码", widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password") != cleaned.get("confirm_password"):
            raise forms.ValidationError("两次输入的新密码不一致")
        return cleaned
