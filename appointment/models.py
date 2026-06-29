from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Department(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="科室名称")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "科室"
        verbose_name_plural = "科室"
        ordering = ["id"]

    def __str__(self):
        return self.name

class Doctor(models.Model):
    TITLE_CHOICES = [
        ("主治医师", "主治医师"),
        ("副主任医师", "副主任医师"),
        ("主任医师", "主任医师"),
    ]
    name = models.CharField(max_length=50, verbose_name="姓名")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="所属科室")
    title = models.CharField(max_length=20, choices=TITLE_CHOICES, verbose_name="职称")
    avatar = models.URLField(max_length=200, blank=True, verbose_name="头像URL")
    phone = models.CharField(max_length=20, verbose_name="联系电话")
    intro = models.TextField(blank=True, verbose_name="简介")
    status = models.SmallIntegerField(default=1, choices=[(1, "在职"), (0, "离职")], verbose_name="状态")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "医生"
        verbose_name_plural = "医生"
        ordering = ["-status", "id"]

    def __str__(self):
        return f"{self.name} ({self.department.name})"

class Schedule(models.Model):
    WEEK_DAY_CHOICES = [
        (0, "周一"), (1, "周二"), (2, "周三"), (3, "周四"),
        (4, "周五"), (5, "周六"), (6, "周日"),
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="医生")
    week_day = models.SmallIntegerField(choices=WEEK_DAY_CHOICES, verbose_name="星期")
    start_time = models.TimeField(verbose_name="上班时间")
    end_time = models.TimeField(verbose_name="下班时间")
    max_patients = models.IntegerField(default=20, verbose_name="最大接诊人数")
    is_off = models.BooleanField(default=False, verbose_name="是否休息")

    class Meta:
        verbose_name = "排班"
        verbose_name_plural = "排班"
        unique_together = ["doctor", "week_day"]

    def __str__(self):
        if self.is_off:
            return f"{self.doctor.name} - {self.get_week_day_display()} 休息"
        return f"{self.doctor.name} - {self.get_week_day_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"

class Patient(models.Model):
    GENDER_CHOICES = [(0, "女"), (1, "男")]
    name = models.CharField(max_length=50, verbose_name="姓名")
    gender = models.SmallIntegerField(choices=GENDER_CHOICES, verbose_name="性别")
    birthday = models.DateField(verbose_name="出生日期")
    phone = models.CharField(max_length=20, verbose_name="手机号")
    id_card = models.CharField(max_length=18, verbose_name="身份证号")
    address = models.TextField(blank=True, verbose_name="地址")
    allergy_history = models.TextField(blank=True, verbose_name="过敏史")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "患者"
        verbose_name_plural = "患者"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.name} ({self.phone})"

class Appointment(models.Model):
    STATUS_CHOICES = [
        (0, "待确认"), (1, "已确认"), (2, "就诊中"),
        (3, "已完成"), (4, "已取消"), (5, "爽约"),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="患者")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="医生")
    appointment_date = models.DateField(verbose_name="预约日期")
    appointment_time = models.TimeField(verbose_name="预约时间")
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=0, verbose_name="状态")
    symptom = models.TextField(blank=True, verbose_name="症状描述")
    remark = models.TextField(blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "预约"
        verbose_name_plural = "预约"
        ordering = ["-appointment_date", "-appointment_time"]

    def __str__(self):
        return f"{self.patient.name} - {self.doctor.name} {self.appointment_date}"

class MedicalRecord(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, verbose_name="关联预约")
    diagnosis = models.TextField(verbose_name="诊断结果")
    prescription = models.TextField(blank=True, verbose_name="处方/用药建议")
    notes = models.TextField(blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="就诊时间")

    class Meta:
        verbose_name = "病历"
        verbose_name_plural = "病历"
        ordering = ["-created_at"]

    def __str__(self):
        return f"病历 - {self.appointment.patient.name} ({self.created_at:%Y-%m-%d})"

class ChargeItem(models.Model):
    CATEGORY_CHOICES = [("挂号费", "挂号费"), ("诊疗费", "诊疗费"), ("检查费", "检查费"), ("药费", "药费")]
    name = models.CharField(max_length=50, verbose_name="项目名称")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="金额")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="类别")

    class Meta:
        verbose_name = "收费项目"
        verbose_name_plural = "收费项目"

    def __str__(self):
        return f"{self.name} - \u00a5{self.price}"

class Order(models.Model):
    STATUS_CHOICES = [(0, "待支付"), (1, "已支付")]
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, verbose_name="关联预约")
    charge_item = models.ForeignKey(ChargeItem, on_delete=models.CASCADE, verbose_name="收费项目")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="实收金额")
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=0, verbose_name="支付状态")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="支付时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "订单"
        verbose_name_plural = "订单"
        ordering = ["-created_at"]

    def __str__(self):
        return f"订单#{self.id} - {self.appointment.patient.name}"
