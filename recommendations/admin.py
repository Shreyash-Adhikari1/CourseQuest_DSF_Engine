from django.contrib import admin
from .models import Recommendation, RecommendationCriterionResult


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['id', 'assessment', 'primary_pathway', 'secondary_pathway', 'tertiary_pathway', 'generated_at']
    search_fields = ['primary_pathway']


@admin.register(RecommendationCriterionResult)
class RecommendationCriterionResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'recommendation', 'criterion_name', 'result_type']
    list_filter = ['result_type', 'criterion_name']