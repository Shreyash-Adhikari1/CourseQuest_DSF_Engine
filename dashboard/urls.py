from django.urls import path
from . import views

urlpatterns = [
    path('', views.global_dashboard, name='global_dashboard'),
    path('report/<int:test_taker_id>/', views.individual_report, name='individual_report'),
    path('report/<int:test_taker_id>/pdf/', views.download_pdf, name='download_pdf'),
    path('report/<int:test_taker_id>/email/', views.send_report_email, name='send_report_email'),
]