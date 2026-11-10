import uuid
from functools import wraps
from urllib.parse import urlencode

from django.db import IntegrityError, transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Exam, Choice, Student, Attempt
from .forms import IdentifyForm

COOKIE = "student_id"
COOKIE_AGE = 60 * 60 * 24 * 365 * 2


def student_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        try:
            sid = uuid.UUID(request.get_signed_cookie(COOKIE, default=""))
            request.student = Student.objects.get(pk=sid)
        except (ValueError, Student.DoesNotExist):
            url = reverse("exams:identify")
            if request.method in ("GET", "HEAD"):
                url += "?" + urlencode({"next": request.get_full_path()})
            return redirect(url)
        return view(request, *args, **kwargs)

    return wrapper


def identify(request):
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure
    ):
        next_url = reverse("exams:index")

    form = IdentifyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            student = Student.objects.create(name=form.cleaned_data["name"])
        except IntegrityError:
            form.add_error("name", "That name is already taken")
        else:
            response = redirect(next_url)
            response.set_signed_cookie(
                COOKIE,
                str(student.id),
                max_age=COOKIE_AGE,
                httponly=True,
                samesite="lax",
            )
            return response
    return render(request, "exams/identify.html", {"form": form, "next": next_url})


class IndexView(generic.ListView):
    template_name = "exams/index.html"
    context_object_name = "latest_exam_list"

    def get_queryset(self):
        """
        Return the last five published exams (not including those set to be published in the future)
        """
        return Exam.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[
            :5
        ]


@method_decorator(student_required, name="dispatch")
class DetailView(generic.DetailView):
    model = Exam
    template_name = "exams/detail.html"

    def get(self, request, *args, **kwargs):
        if Attempt.objects.filter(
            student=request.student, exam_id=kwargs["pk"]
        ).exists():
            return redirect("exams:results", kwargs["pk"])
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Excludes exams not published yet
        """
        return Exam.objects.filter(pub_date__lte=timezone.now())


@method_decorator(student_required, name="dispatch")
class ResultsView(generic.DetailView):
    model = Exam
    template_name = "exams/results.html"

    def get_queryset(self):
        """
        Excludes exams not published yet (mentioned in the tutorial with no example, doing it here cus I probably should.)
        """
        return Exam.objects.filter(pub_date__lte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mchoices = self.object.multiplechoice_set.prefetch_related("choice_set")
        context["attempt"] = Attempt.objects.filter(
            student=self.request.student, exam=self.object
        ).first()
        context["charts"] = [
            {
                "mchoice": m.mchoice_text,
                "labels": [c.choice_text for c in m.choice_set.all()],
                "votes": [c.answered for c in m.choice_set.all()],
            }
            for m in mchoices
        ]
        return context


"""
Blocks someone triggering the vote logic without going through detail and voting.
"""


@require_POST
@student_required
def vote(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, pub_date__lte=timezone.now())

    """
    Check choices and validate before touching database.
    """
    choices = []
    for mchoice in exam.multiplechoice_set.all():
        try:
            choices.append(
                mchoice.choice_set.get(pk=request.POST.get(f"choice{mchoice.id}"))
            )
        except (Choice.DoesNotExist, ValueError):
            messages.error(request, f"Please answer: {mchoice.mchoice_text}")
            return redirect("exams:detail", exam_id)

    score = sum(1 for c in choices if c.correct)

    try:
        with transaction.atomic():
            Attempt.objects.create(
                student=request.student, exam=exam, score=score, total=len(choices)
            )
            Choice.objects.filter(pk__in=[c.pk for c in choices]).update(
                answered=F("answered") + 1
            )
    except IntegrityError:
        messages.info(request, "You've already taken this exam")

    return redirect("exams:results", exam_id)
