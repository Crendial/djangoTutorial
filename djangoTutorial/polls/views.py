import uuid

from django.db import IntegrityError, transaction
from django.db.models import F
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.contrib import messages

from .models import Poll, Question, Choice, Vote

class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_poll_list"

    def get_queryset(self):
        """
        Return the last five published polls (not including those set to be published in the future)
        """
        return Poll.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]

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
        choices = self.object.choice_set.all()
        context["choices"] = [c.choice_text for c in choices]
        context["votes"] = [c.votes for c in choices]
        return context

def vote(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll.id)

    try:
        voter_id = uuid.UUID(request.get_signed_cookie("voter_id", default=""))
        new_cookie = False
    except ValueError:
        voter_id, new_cookie = uuid.uuid4(), True

    try:
        with transaction.atomic():
            Vote.objects.create(poll=poll, voter_id=voter_id)
    except IntegrityError:
        messages.info(request, "Yo've already voted on this poll.")
        return redirect("polls:results", poll_id)

    response = redirect("polls:results", poll.id)
    if new_cookie:
        response.set_signed_cookie("voter_id", str(voter_id),
                                   max_age=60*60*24*365*2, httponly=True, samesite="Lax")
    return response