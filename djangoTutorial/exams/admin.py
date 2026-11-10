from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.core.exceptions import ValidationError
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
    list_display = ["exam_text", "pub_date", "was_published_recently", "show_qr_code"]
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

    def get_urls(self):
        custom = [
            path(
                "<int:pk>/qr/",
                self.admin_site.admin_view(self.qr_view),
                name="exams_exam_qr",
            ),
        ]
        return custom + super().get_urls()

    def qr_view(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        url = request.build_absolute_uri(reverse("exams:detail", args=(exam.pk,)))
        return TemplateResponse(
            request, "admin/exams/exam/qr.html", {"exam": exam, "url": url}
        )


admin.site.register(Exam, ExamAdmin)
admin.site.register(Student)
admin.site.register(Attempt)
