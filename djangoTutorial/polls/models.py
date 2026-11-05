import datetime
from django.db import models
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import admin

# Create your models here.

class Poll(models.Model):
    poll_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date publisehed")

    def __str__(self):
        return self.poll_text

    @admin.display(
        boolean=True,
        ordering="pub_date",
        description="Published recently?",
    )

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

class Question(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, null=True, blank=True)
    question_text = models.CharField(max_length=200)

    def __str__(self):
        return self.question_text
    
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text

class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    voter_id = models.UUIDField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["poll", "voter_id"], name="one_vote_per_voter")
        ]