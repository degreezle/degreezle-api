from django.urls import path
from . import views

urlpatterns = [
    # path('', views.index, name='index'),
    path(r'crew/<int:movie_id>', views.CrewMemberAPI.as_view()),
]