from django.contrib import admin
from .models import Pathway, PathwayRelevance, PathwayScore


@admin.register(Pathway)
class PathwayAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description']
    search_fields = ['name']


@admin.register(PathwayRelevance)
class PathwayRelevanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'pathway', 'criterion_name', 'relevance_score']
    list_filter = ['pathway', 'criterion_name']
    search_fields = ['criterion_name']


@admin.register(PathwayScore)
class PathwayScoreAdmin(admin.ModelAdmin):
    list_display = ['id', 'assessment', 'pathway', 'knowledge_score', 'preference_score', 'final_score']
    list_filter = ['pathway']