from django.db import models
from assessments.models import Assessment


# One row per assessment. Stores the final verdict —
# which pathway is primary, secondary, tertiary, and
# the LLM explanation (blank until RAG+LLM fills it in).
class Recommendation(models.Model):
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE)
    primary_pathway = models.CharField(max_length=100)
    secondary_pathway = models.CharField(max_length=100)
    tertiary_pathway = models.CharField(max_length=100)
    explanation = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assessment {self.assessment.test_taker_id} → {self.primary_pathway}"


# One row per criterion result per recommendation.
# Kept separate so aggregate analytics queries work cleanly —
# e.g. most common strengths across all students.
class RecommendationCriterionResult(models.Model):

    RESULT_TYPES = [
        ('strength', 'Strength'),
        ('improvement', 'Improvement'),
    ]

    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE)
    criterion_name = models.CharField(max_length=50)
    result_type = models.CharField(max_length=20, choices=RESULT_TYPES)

    def __str__(self):
        return f"{self.criterion_name} - {self.result_type}"