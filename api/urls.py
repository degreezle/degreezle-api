from django.urls import path
from . import views

urlpatterns = [
    path(r'movie/<int:movie_id>/', views.MovieInfoAPI.as_view()),
    path(r'movie/<int:movie_id>/crew/', views.MovieCrewAPI.as_view()),
    path(r'person/<int:person_id>/', views.PersonInfoAPI.as_view()),
    path(r'person/<int:person_id>/filmography/', views.FilmographyAPI.as_view()),
    path(r'puzzle/init/', views.InitPuzzleAPI.as_view()),
    path(r'solution/', views.SolutionAPI.as_view()), 
    path(r'solution/<str:token>/', views.SolutionAPI.as_view()),
]
