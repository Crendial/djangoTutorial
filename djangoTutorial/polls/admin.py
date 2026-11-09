from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from nested_admin import NestedTabularInline, NestedModelAdmin

# Register your models here.
from .models import Poll, Question, Choice


class ChoiceInline(NestedTabularInline):
    model = Choice
    extra = 2
    min_num = 2
    validate_min = True


class QuestionInline(NestedTabularInline):
    model = Question
    extra = 1
    min_num = 1
    validate_min = True
    inlines = [ChoiceInline]


class PollAdmin(NestedModelAdmin):
    class Media:
        css = {"all": ("polls/admin_fix.css",)}

    fieldsets = [
        (None, {"fields": ["poll_text"]}),
        ("Date information", {"fields": ["pub_date"], "classes": ["collapse"]}),
    ]
    inlines = [QuestionInline]

    search_fields = ["poll_text"]
    list_display = ["poll_text", "pub_date", "was_published_recently", "show_qr_code"]
    list_filter = ["pub_date"]

    @admin.display(description="QR code")
    def show_qr_code(self, obj):
        url = reverse("admin:polls_poll_qr", args=(obj.pk,))
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
                name="polls_poll_qr",
            ),
        ]
        return custom + super().get_urls()

    def qr_view(self, request, pk):
        poll = get_object_or_404(Poll, pk=pk)
        url = request.build_absolute_uri(reverse("polls:detail", args=(poll.pk,)))
        return TemplateResponse(
            request, "admin/polls/poll/qr.html", {"poll": poll, "url": url}
        )


admin.site.register(Poll, PollAdmin)

