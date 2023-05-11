from django.urls import path
from crontab.views import CrontabView

urlpatterns = [
    path('run-cron/', CrontabView.as_view()),
]