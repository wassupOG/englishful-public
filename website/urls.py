from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

#1st route, 2nd view to render
urlpatterns = [
    ### BASICS ###
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("free_tests", views.free_tests, name="free_tests"),
    path("free_tests/<slug:free_testname>", views.single_test_free, name="single_test_free"),
    path("free_tests/<slug:free_testname>/result", views.free_check, name="free_check"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("tests", views.all_tests, name="tests"),
    ### BASICS END ###

    ### DICTIONARY ###
    path('dictionary', views.dictionary, name='dictionary'),
    path('dictionary/add', views.add_word, name="add_word"),
    path('dictionary/filter', views.dictionary_filter, name="dictionary_filter"),
    path('dictionary/search', views.dictionary_search, name="dictionary_search"),
    path('add-words', views.add_delete_words, name="add_delete_words"),
    path('dictionary_edit', views.dictionary_edit, name="dictionary_edit"),
    path('update_progress', views.update_progress, name="update_progress"),
    ### DICTIONARY END ###

    ### TESTS ###
    path("results", views.results, name="results"),
    path("results_edit", views.results_edit, name="results_edit"),
    path("tests/<slug:testname>", views.single_test, name="single_test"),
    path("tests/<slug:testname>/result", views.lower, name="lower_check"),
    path("results/<slug:testname>", views.solved_test, name="solved_test"),
    path("results/<slug:testname>/<int:student_id>/", views.solved_test_teacher, name="solved_test_teacher"),
    ### TESTS END ###

    ### EGE ###
    path("ege", views.ege_tests, name="ege_tests"),
    path("ege/<slug:ege_testname>", views.ege_single_test, name="ege_single_test"),
    path("ege/<slug:ege_testname>/result", views.ege_check, name="ege_check"),
    path("results/<slug:ege_testname>/result",views.ege_result, name="ege_result"),
    path("results/<slug:ege_testname>/<int:student_id>",views.ege_result_admin, name="ege_result_admin"),
    path('speaking/<slug:ege_testname>', views.save_audio, name='save_audio'),
    path("download", views.download_audio, name="download_audio"),
    ### EGE END ###

    ### FREE ###
    path("theory", views.theory, name="theory"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)