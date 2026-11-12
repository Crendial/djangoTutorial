import uuid

from django.db import IntegrityError, transaction
from django.db.models import F, Count
from django.shortcuts import get_object_or_404, redirect
from django.views import generic
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages

from .models import Poll, Choice, Vote


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_poll_list"

    def get_queryset(self):
        """
        Return the last five published polls (not including those set to be published in the future)
        """
        return Poll.objects.annotate(question_count=Count("question")).order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    model = Poll
    template_name = "polls/detail.html"

    def get(self, request, *args, **kwargs):
        poll = self.get_object()
        try:
            voter_id = uuid.UUID(request.get_signed_cookie("voter_id", default=""))
        except ValueError:
            voter_id = None
        if voter_id and Vote.objects.filter(poll=poll, voter_id=voter_id).exists():
            return redirect("polls:results", poll.id)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Excludes polls not published yet
        """
        return Poll.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Poll
    template_name = "polls/results.html"

    def get_queryset(self):
        """
        Excludes polls not published yet (mentioned in the tutorial with no example, doing it here cus I probably should.)
        """
        return Poll.objects.filter(pub_date__lte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        questions = self.object.question_set.prefetch_related("choice_set")
        context["charts"] = [
            {
                "question": q.question_text,
                "labels": [c.choice_text for c in q.choice_set.all()],
                "votes": [c.votes for c in q.choice_set.all()],
            }
            for q in questions
        ]
        return context


"""
Blocks someone triggering the vote logic without going through detail and voting.
"""


@require_POST
def vote(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id, pub_date__lte=timezone.now())

    """
    Check who is voting.
    """
    try:
        voter_id = uuid.UUID(request.get_signed_cookie("voter_id", default=""))
        new_cookie = False
    except ValueError:
        voter_id, new_cookie = uuid.uuid4(), True

    """
    Check choices and validate before touching database.
    """
    choices = []
    for question in poll.question_set.all():
        try:
            choices.append(
                question.choice_set.get(pk=request.POST.get(f"choice{question.id}"))
            )
        except (Choice.DoesNotExist, ValueError):
            messages.error(request, f"Please answer: {question.question_text}")
            return redirect("polls:detail", poll_id)

    try:
        with transaction.atomic():
            Vote.objects.create(poll=poll, voter_id=voter_id)
            for choice in choices:
                Choice.objects.filter(pk=choice.pk).update(votes=F("votes") + 1)
    except IntegrityError:
        messages.info(request, "You've already voted on this poll.")
        return redirect("polls:results", poll_id)

    response = redirect("polls:results", poll_id)
    if new_cookie:
        response.set_signed_cookie(
            "voter_id",
            str(voter_id),
            max_age=60 * 60 * 24 * 365 * 2,
            httponly=True,
            samesite="Lax",
        )
    return response
