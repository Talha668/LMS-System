from django.urls import path
from . import views





urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('course/<int:course_id>/dashboard/', views.course_dashboard, name='course_dashboard'),
    path('course/<int:course_id>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    # Rating URLs
    path('course/<int:course_id>/rate/', views.add_rating, name='add_rating'),
    # Quiz URLs
    path('course/<int:course_id>/lesson/<int:lesson_id>/quiz/start/', views.start_quiz, name='start_quiz'),
    path('course/<int:course_id>/lesson/<int:lesson_id>/quiz/<int:attempt_id>/', views.take_quiz, name='take_quiz'),
    path('course/<int:course_id>/lesson/<int:lesson_id>/quiz/<int:attempt_id>/finish/', views.finish_quiz, name='finish_quiz'),
    path('course/<int:course_id>/lesson/<int:lesson_id>/quiz/<int:attempt_id>/results/', views.quiz_results, name='quiz_results'),
    # Certificate URLs
    path('course/<int:course_id>/certificate/', views.generate_certificate, name='generate_certificate'),
    path('my-certificates/', views.my_certificates, name='my_certificates'),
    # Discussion URLs
    path('course/<int:course_id>/discussions/', views.course_discussions, name='course_discussions'),
    path('course/<int:course_id>/discussions/<int:thread_id>/', views.discussion_thread, name='discussion_thread'),
    path('course/<int:course_id>/discussions/<int:thread_id>/reply/<int:reply_id>/mark-answer/', views.mark_as_answer, name='mark_as_answer'),
    # Learning Path URLs
    path('learning_path/', views.learning_path_list, name='learning_path_list'),
    path('learning_path/<slug:slug>/', views.learning_path_detail, name='learning_path_detail'),
    path('learning_path/<slug:slug>/enroll/', views.enroll_learning_path, name='enroll_learning_path'),
    # Bokkmark  URLs
    path('lesson/<int:lesson_id>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('bookmarks/', views.my_bookmarks, name='my_bookmarks'),
    # Anamytics URLs
    path('analytics/course/<int:course_id>/', views.course_analytics, name='course_analytics'),
    path('analytics/my-progress/', views.my_progress, name='my_progress'),
    # Payment URLs
    path('payment/initiate/<int:course_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/success/<int:course_id>/', views.payment_success, name='payment_success'),
    path('payment/cancel/<int:course_id>/', views.payment_cancel, name='payment_cancel'),
    path('payment/webhook/', views.lemon_squeezy_webhook, name='lemon_squeezy_webhook'),
]