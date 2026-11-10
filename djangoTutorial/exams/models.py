import datetime
import uuid
from django.db import models
from django.utils import timezone
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower

# Create your models here.


class Exam(models.Model):
    exam_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date publisehed")

    def __str__(self):
        return self.exam_text

    @admin.display(
        boolean=True,
        ordering="pub_date",
        description="Published recently?",
    )
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class MultipleChoice(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    mchoice_text = models.CharField(max_length=200)

    def __str__(self):
        return self.mchoice_text


class Choice(models.Model):
    mchoice = models.ForeignKey(MultipleChoice, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    answered = models.PositiveIntegerField(default=0)
    correct = models.BooleanField(default=False)

    def __str__(self):
        return self.choice_text


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [UniqueConstraint(Lower("name"), name="unique_student_name_ci")]

    def __str__(self):
        return self.name


class Attempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    score = models.PositiveBigIntegerField()
    total = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["student", "exam"], name="one_attempt_per_student")
        ]
