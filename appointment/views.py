import json
from datetime import date, timedelta, datetime
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from .models import Department, Doctor, Schedule, Patient, Appointment, MedicalRecord, ChargeItem, Order
from .forms import (
    LoginForm, DoctorForm, PatientForm, AppointmentForm,
    MedicalRecordForm, OrderForm, ChargeItemForm, DepartmentForm,
    PasswordChangeForm,
)

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user:
                login(request, user)
                return redirect("dashboard")
            messages.error(request, "用户名或密码错误")
    else:
        form = LoginForm()
    return render(request, "appointment/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("login")

# ==================== HELPERS ====================
def active_doctors():
    return Doctor.objects.filter(status=1)

# ==================== DASHBOARD ====================
@login_required
def dashboard(request):
    today = timezone.localdate()
    today_appts = Appointment.objects.filter(appointment_date=today)
    pending = today_appts.filter(status=0).count()
    total_today = today_appts.count()
    income_today = Order.objects.filter(
        appointment__appointment_date=today, status=1
    ).aggregate(total=Sum("amount"))["total"] or 0
    new_patients_today = Patient.objects.filter(created_at__date=today).count()

    last_7 = [today - timedelta(days=i) for i in range(6, -1, -1)]
    trend_labels = [d.strftime("%m/%d") for d in last_7]
    trend_data = []
    for d in last_7:
        trend_data.append(Appointment.objects.filter(appointment_date=d).count())

    dept_data = []
    for dept in Department.objects.all():
        count = Appointment.objects.filter(
            doctor__department=dept, appointment_date=today
        ).count()
        if count > 0:
            dept_data.append({"name": dept.name, "value": count})
    if not dept_data:
        dept_data = [{"name": "暂无数据", "value": 1}]

    recent_appts = today_appts.filter(status__in=[0, 1]).order_by("appointment_time")[:5]

    context = {
        "total_today": total_today,
        "pending_count": pending,
        "income_today": float(income_today),
        "new_patients": new_patients_today,
        "trend_labels": json.dumps(trend_labels),
        "trend_data": json.dumps(trend_data),
        "dept_data": json.dumps(dept_data),
        "recent_appts": recent_appts,
    }
    return render(request, "appointment/dashboard.html", context)

# ==================== DOCTORS ====================
@login_required
def doctor_list(request):
    q = request.GET.get("q", "")
    doctors = Doctor.objects.all()
    if q:
        doctors = doctors.filter(Q(name__icontains=q) | Q(phone__icontains=q))
    page = int(request.GET.get("page", 1))
    page_size = 10
    total = doctors.count()
    start = (page - 1) * page_size
    end = start + page_size
    doctors = doctors.order_by("-status", "id")[start:end]
    total_pages = (total + page_size - 1) // page_size
    return render(request, "appointment/doctors/list.html", {
        "doctors": doctors, "q": q, "page": page,
        "total_pages": total_pages, "total": total, "page_range": range(1, total_pages + 1),
    })

@login_required
def doctor_add(request):
    if request.method == "POST":
        form = DoctorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "医生添加成功")
            return redirect("doctor_list")
    else:
        form = DoctorForm()
    return render(request, "appointment/doctors/form.html", {"form": form, "title": "新增医生"})

@login_required
def doctor_edit(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == "POST":
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "医生信息已更新")
            return redirect("doctor_list")
    else:
        form = DoctorForm(instance=doctor)
    return render(request, "appointment/doctors/form.html", {"form": form, "title": "编辑医生"})

@login_required
def doctor_delete(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if Appointment.objects.filter(doctor=doctor).exists():
        messages.error(request, "该医生已有预约记录，不可删除")
        return redirect("doctor_list")
    if request.method == "POST":
        doctor.status = 0
        doctor.save()
        messages.success(request, "医生已设为离职")
        return redirect("doctor_list")
    return render(request, "appointment/doctors/delete.html", {"doctor": doctor})

# ==================== SCHEDULES ====================
@login_required
def schedule_list(request):
    doctors = active_doctors()
    week_days = Schedule.WEEK_DAY_CHOICES
    schedules = Schedule.objects.filter(doctor__in=doctors)
    # Build schedule lookup and create rows for template
    schedule_lookup = {}
    for s in schedules:
        schedule_lookup[(s.doctor_id, s.week_day)] = s
    schedule_rows = []
    for doc in doctors:
        row = {"doctor": doc}
        for wk in range(7):
            row[str(wk)] = schedule_lookup.get((doc.id, wk))
        schedule_rows.append(row)
    if request.method == "POST":
        doctor_id = request.POST.get("doctor")
        week_day = int(request.POST.get("week_day", 0))
        is_off = request.POST.get("is_off") == "on"
        start_time = request.POST.get("start_time") or None
        end_time = request.POST.get("end_time") or None
        max_patients = request.POST.get("max_patients") or 20
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        schedule, created = Schedule.objects.get_or_create(
            doctor=doctor, week_day=week_day,
            defaults={"start_time": "08:00", "end_time": "17:00", "max_patients": 20, "is_off": False},
        )
        schedule.is_off = is_off
        if not is_off and start_time and end_time:
            schedule.start_time = start_time
            schedule.end_time = end_time
            schedule.max_patients = int(max_patients)
        elif is_off:
            schedule.start_time = "00:00"
            schedule.end_time = "00:00"
            schedule.max_patients = 0
        schedule.save()
        messages.success(request, "排班已更新")
        return redirect("schedule_list")
    return render(request, "appointment/schedules/list.html", {
        "doctors": doctors, "week_days": week_days, "schedule_rows": schedule_rows,
    })

@login_required
def schedule_update(request):
    return schedule_list(request)

# ==================== PATIENTS ====================
@login_required
def patient_list(request):
    q = request.GET.get("q", "")
    patients = Patient.objects.all()
    if q:
        patients = patients.filter(Q(name__icontains=q) | Q(phone__icontains=q))
    page = int(request.GET.get("page", 1))
    page_size = 10
    total = patients.count()
    start = (page - 1) * page_size
    end = start + page_size
    patients = patients.order_by("-id")[start:end]
    total_pages = (total + page_size - 1) // page_size
    return render(request, "appointment/patients/list.html", {
        "patients": patients, "q": q, "page": page,
        "total_pages": total_pages, "total": total, "page_range": range(1, total_pages + 1),
    })

@login_required
def patient_add(request):
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "患者添加成功")
            return redirect("patient_list")
    else:
        form = PatientForm()
    return render(request, "appointment/patients/form.html", {"form": form, "title": "新增患者"})

@login_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "患者信息已更新")
            return redirect("patient_list")
    else:
        form = PatientForm(instance=patient)
    return render(request, "appointment/patients/form.html", {"form": form, "title": "编辑患者"})

@login_required
def patient_history(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    appointments = Appointment.objects.filter(patient=patient).order_by("-appointment_date")
    medical_records = MedicalRecord.objects.filter(appointment__patient=patient).order_by("-created_at")
    return render(request, "appointment/patients/history.html", {
        "patient": patient, "appointments": appointments, "medical_records": medical_records,
    })

# ==================== APPOINTMENTS ====================
@login_required
def appointment_list(request):
    appts = Appointment.objects.all()
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    status_filter = request.GET.get("status", "")
    doctor_id = request.GET.get("doctor", "")
    q = request.GET.get("q", "")

    if date_from:
        appts = appts.filter(appointment_date__gte=date_from)
    if date_to:
        appts = appts.filter(appointment_date__lte=date_to)
    if status_filter:
        appts = appts.filter(status=int(status_filter))
    if doctor_id:
        appts = appts.filter(doctor_id=int(doctor_id))
    if q:
        appts = appts.filter(Q(patient__name__icontains=q) | Q(doctor__name__icontains=q))

    page = int(request.GET.get("page", 1))
    page_size = 10
    total = appts.count()
    start = (page - 1) * page_size
    end = start + page_size
    appts = appts.order_by("-appointment_date", "-appointment_time")[start:end]
    total_pages = (total + page_size - 1) // page_size

    doctors = active_doctors()
    status_choices = Appointment.STATUS_CHOICES
    return render(request, "appointment/appointments/list.html", {
        "appointments": appts, "doctors": doctors, "status_choices": status_choices,
        "q": q, "page": page, "total_pages": total_pages, "total": total, "page_range": range(1, total_pages + 1),
        "date_from": date_from, "date_to": date_to,
        "status_filter": status_filter, "doctor_id": doctor_id,
    })

@login_required
def appointment_add(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "预约创建成功")
            return redirect("appointment_list")
    else:
        form = AppointmentForm()
        doctor_id = request.GET.get("doctor")
        if doctor_id:
            form.fields["doctor"].initial = doctor_id
    return render(request, "appointment/appointments/form.html", {"form": form, "title": "新增预约"})

@login_required
def appointment_edit(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    if appt.status not in [0, 1]:
        messages.error(request, "当前状态不可编辑")
        return redirect("appointment_list")
    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appt)
        if form.is_valid():
            form.save()
            messages.success(request, "预约已更新")
            return redirect("appointment_list")
    else:
        form = AppointmentForm(instance=appt)
    return render(request, "appointment/appointments/form.html", {"form": form, "title": "编辑预约"})

VALID_TRANSITIONS = {
    0: [1, 4],  # pending -> confirmed or cancelled
    1: [2, 5],  # confirmed -> in_progress or no_show
    2: [3],     # in_progress -> completed
}

@login_required
def appointment_update_status(request, pk, status):
    appt = get_object_or_404(Appointment, pk=pk)
    if status not in VALID_TRANSITIONS.get(appt.status, []):
        messages.error(request, "无效的状态变更")
        return redirect("appointment_list")
    if status == 1 and request.method == "POST":
        appt.status = status
        appt.save()
        reg_item = ChargeItem.objects.filter(category="挂号费").first()
        if reg_item:
            Order.objects.get_or_create(
                appointment=appt,
                charge_item=reg_item,
                defaults={"amount": reg_item.price, "status": 0},
            )
        consult_fee_map = {"主治医师": Decimal("20.00"), "副主任医师": Decimal("50.00"), "主任医师": Decimal("100.00")}
        fee = consult_fee_map.get(appt.doctor.title, Decimal("20.00"))
        consult_item, _ = ChargeItem.objects.get_or_create(
            name=f"诊疗费({appt.doctor.title})", defaults={"price": fee, "category": "诊疗费"},
        )
        if consult_item.price != fee:
            consult_item.price = fee
            consult_item.save()
        Order.objects.get_or_create(
            appointment=appt,
            charge_item=consult_item,
            defaults={"amount": consult_item.price, "status": 0},
        )
        messages.success(request, "预约已确认，收费订单已生成")
    elif status == 3:
        if not MedicalRecord.objects.filter(appointment=appt).exists():
            messages.warning(request, "请先创建病历再完成就诊")
            return redirect("medical_record_add")
        appt.status = status
        appt.save()
        messages.success(request, "就诊已完成")
    else:
        appt.status = status
        appt.save()
        label = dict(Appointment.STATUS_CHOICES).get(status, "")
        messages.success(request, f"预约状态已变更为: {label}")
    return redirect("appointment_list")

# ==================== MEDICAL RECORDS ====================
@login_required
def medical_record_list(request):
    records = MedicalRecord.objects.select_related("appointment__patient", "appointment__doctor").all()
    q = request.GET.get("q", "")
    if q:
        records = records.filter(
            Q(appointment__patient__name__icontains=q) |
            Q(appointment__doctor__name__icontains=q)
        )
    page = int(request.GET.get("page", 1))
    page_size = 10
    total = records.count()
    start = (page - 1) * page_size
    end = start + page_size
    records = records.order_by("-created_at")[start:end]
    total_pages = (total + page_size - 1) // page_size
    return render(request, "appointment/medical_records/list.html", {
        "records": records, "q": q, "page": page,
        "total_pages": total_pages, "total": total, "page_range": range(1, total_pages + 1),
    })

@login_required
def medical_record_add(request):
    if request.method == "POST":
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            form.save()
            appt = form.cleaned_data["appointment"]
            if appt.status == 1:
                appt.status = 2
                appt.save()
            messages.success(request, "病历创建成功")
            return redirect("medical_record_list")
    else:
        form = MedicalRecordForm()
        appt_id = request.GET.get("appointment")
        if appt_id:
            form.fields["appointment"].initial = appt_id
            form.fields["appointment"].queryset = Appointment.objects.filter(status__in=[1, 2])
        else:
            form.fields["appointment"].queryset = Appointment.objects.filter(status__in=[1, 2])
    return render(request, "appointment/medical_records/form.html", {"form": form, "title": "创建病历"})

@login_required
def medical_record_edit(request, pk):
    record = get_object_or_404(MedicalRecord, pk=pk)
    if request.method == "POST":
        form = MedicalRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "病历已更新")
            return redirect("medical_record_list")
    else:
        form = MedicalRecordForm(instance=record)
        form.fields["appointment"].queryset = Appointment.objects.filter(status__in=[1, 2, 3])
    return render(request, "appointment/medical_records/form.html", {"form": form, "title": "编辑病历"})

# ==================== ORDERS ====================
@login_required
def order_list(request):
    orders = Order.objects.select_related("appointment__patient", "appointment__doctor", "charge_item").all()
    status_filter = request.GET.get("status", "")
    if status_filter:
        orders = orders.filter(status=int(status_filter))
    page = int(request.GET.get("page", 1))
    page_size = 10
    total = orders.count()
    start = (page - 1) * page_size
    end = start + page_size
    orders = orders.order_by("-created_at")[start:end]
    total_pages = (total + page_size - 1) // page_size
    return render(request, "appointment/orders/list.html", {
        "orders": orders, "page": page, "total_pages": total_pages, "total": total, "page_range": range(1, total_pages + 1),
        "status_filter": status_filter,
    })

@login_required
def order_add(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "订单创建成功")
            return redirect("order_list")
    else:
        form = OrderForm()
    return render(request, "appointment/orders/form.html", {"form": form, "title": "新增订单"})

@login_required
def order_pay(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status == 1:
        messages.info(request, "该订单已支付")
    else:
        order.status = 1
        order.paid_at = timezone.now()
        order.save()
        messages.success(request, "支付成功")
    return redirect("order_list")

@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.delete()
    messages.success(request, "订单已删除")
    return redirect("order_list")

# ==================== SETTINGS ====================
@login_required
def settings_index(request):
    departments = Department.objects.all()
    return render(request, "appointment/settings/index.html", {"departments": departments})

@login_required
def department_add(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "科室添加成功")
            return redirect("settings_index")
    else:
        form = DepartmentForm()
    return render(request, "appointment/settings/department_form.html", {"form": form, "title": "新增科室"})

@login_required
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, "科室已更新")
            return redirect("settings_index")
    else:
        form = DepartmentForm(instance=dept)
    return render(request, "appointment/settings/department_form.html", {"form": form, "title": "编辑科室"})

@login_required
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if Doctor.objects.filter(department=dept).exists():
        messages.error(request, "该科室下有关联医生，无法删除")
    else:
        dept.delete()
        messages.success(request, "科室已删除")
    return redirect("settings_index")

@login_required
def password_change(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            if not request.user.check_password(form.cleaned_data["old_password"]):
                messages.error(request, "原密码错误")
            else:
                request.user.set_password(form.cleaned_data["new_password"])
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "密码修改成功")
                return redirect("settings_index")
    else:
        form = PasswordChangeForm()
    return render(request, "appointment/settings/password_form.html", {"form": form})
