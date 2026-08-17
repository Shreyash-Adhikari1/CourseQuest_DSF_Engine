from django.contrib import admin
from .models import Assessment, CriterionScore


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'test_taker_id', 'session_id', 'assessment_version', 'submitted_at']
    list_filter = ['assessment_version']
    search_fields = ['test_taker_id', 'session_id']


@admin.register(CriterionScore)
class CriterionScoreAdmin(admin.ModelAdmin):
    list_display = ['id', 'assessment', 'criterion_name', 'value', 'confidence']
    list_filter = ['criterion_name']
    search_fields = ['criterion_name']