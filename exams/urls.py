from django.urls import path

from . import views

app_name = "exams"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("identify/", views.identify, name="identify"),
    path("<int:pk>", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:exam_id>/vote/", views.vote, name="vote"),
]
