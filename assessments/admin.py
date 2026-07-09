from django.contrib import admin
from .models import Assessment, CriterionScore


# What each part does
# @admin.register(Assessment) — registers the model with admin. Replaces the older admin.site.register(Assessment) syntax, cleaner and more modern.
# list_display — which columns show up in the admin list view. Without this Django just shows Assessment object (1) for every row — useless.
# list_filter — adds a filter sidebar on the right so you can filter rows by that field.
# search_fields — adds a search bar at the top so you can search by those fields

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