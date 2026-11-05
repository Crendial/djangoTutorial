from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

# Register your models here.
from .models import Question, Choice

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2
    min_num = 2
    validate_min = True

class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date information", {"fields": ["pub_date"], "classes": ["collapse"]})
    ]
    inlines = [ChoiceInline]

    search_fields = ["question_text"]
    list_display = ["question_text", "pub_date", "was_published_recently", "show_qr_code"]
    list_filter = ["pub_date"]

    @admin.display(description="QR code")
    def show_qr_code(self, obj):
        url = reverse("admin:polls_question_qr", args=(obj.pk,))
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
                name="polls_question_qr",
            ),
        ]
        return custom + super().get_urls()

    def qr_view(self, request, pk):
        question = get_object_or_404(Question, pk=pk)
        url = request.build_absolute_uri(reverse("polls:detail", args=(question.pk,)))
        return TemplateResponse(
            request, "admin/polls/question/qr.html", {"question": question, "url": url}
        )

admin.site.register(Question, QuestionAdmin)