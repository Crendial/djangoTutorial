import json

from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from django.core.exceptions import ValidationError, PermissionDenied
from nested_admin import NestedTabularInline, NestedModelAdmin
from nested_admin.formsets import NestedInlineFormSet

# Register your models here.
from .models import Exam, MultipleChoice, Choice, Student, Attempt


class BaseChoiceFormSet(NestedInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        correct = sum(
            1
            for f in self.forms
            if f.cleaned_data
            and not f.cleaned_data.get("DELETE")
            and f.cleaned_data.get("choice_text")
            and f.cleaned_data.get("correct")
        )
        if correct != 1:
            raise ValidationError("Exactly one choice must be correct.")


class ChoiceInline(NestedTabularInline):
    model = Choice
    formset = BaseChoiceFormSet
    extra = 2
    min_num = 2
    validate_min = True


class MchoiceInline(NestedTabularInline):
    model = MultipleChoice
    extra = 1
    min_num = 1
    validate_min = True
    inlines = [ChoiceInline]


class ExamAdmin(NestedModelAdmin):
    class Media:
        css = {"all": ("polls/admin_fix.css",)}

    fieldsets = [
        (None, {"fields": ["exam_text"]}),
        ("Date information", {"fields": ["pub_date"], "classes": ["collapse"]}),
    ]
    inlines = [MchoiceInline]

    search_fields = ["exam_text"]
    list_display = [
        "exam_text",
        "pub_date",
        "was_published_recently",
        "show_qr_code",
        "show_scores",
    ]
    list_filter = ["pub_date"]

    @admin.display(description="QR code")
    def show_qr_code(self, obj):
        url = reverse("admin:exams_exam_qr", args=(obj.pk,))
        return format_html(
            '<a class="button" href="{}" '
            "onclick=\"window.open(this.href, 'qr', 'width=380,height=480'); return false;\">"
            "Show QR</a>",
            url,
        )

    @admin.display(description="Student scores")
    def show_scores(self, obj):
        url = reverse("admin:exams_exam_scores", args=(obj.pk,))
        return format_html('<a class="button" href="{}">Scores</a>', url)

    def get_urls(self):
        custom = [
            path(
                "<int:pk>/qr/",
                self.admin_site.admin_view(self.qr_view),
                name="exams_exam_qr",
            ),
            path(
                "<int:pk>/scores/",
                self.admin_site.admin_view(self.scores_view),
                name="exams_exam_scores",
            ),
        ]
        return custom + super().get_urls()

    def qr_view(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        url = request.build_absolute_uri(reverse("exams:detail", args=(exam.pk,)))
        return TemplateResponse(
            request, "admin/exams/exam/qr.html", {"exam": exam, "url": url}
        )

    def scores_view(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        if not self.has_view_permission(request, exam):
            raise PermissionDenied
        attempts = (
            Attempt.objects.filter(exam=exam)
            .select_related("student")
            .order_by("-score", "created")
        )
        context = {
            **self.admin_site.each_context(request),
            "title": f"Scores: {exam.exam_text}",
            "opts": self.model._meta,
            "exam": exam,
            "attempts": attempts,
        }
        return TemplateResponse(request, "admin/exams/exam/scores.html", context)

class AttemptAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("polls/admin_fix.css",)}
   
    fields = ("student", "exam", "score", "total", "formatted_answers")
    readonly_fields = ("student", "exam", "score", "total", "formatted_answers")

    @admin.display(description="Student answers")
    def formatted_answers(self, obj):
        if not obj or not obj.answers:
            return "-"

        rows = format_html_join(
            "",
            "<tr><td>{}</td><td>{}</td><td>{}</td></tr>",
            (
                (question, answer, "✔ Correct" if correct else "✘ Wrong")
                for question, (answer, correct) in obj.answers.items()
            ),
        )
        return format_html(
            "<table>"
            "<thead><tr><th>Question</th><th>Answer</th><th>Result</th></tr></thead>"
            "<tbody>{}</tbody>"
            "</table>",
            rows,
        )

admin.site.register(Exam, ExamAdmin)
admin.site.register(Student)
admin.site.register(Attempt, AttemptAdmin)
