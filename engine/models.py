from django.db import models
from assessments.models import Assessment

# Represents one IT specialization (AI, Cybersecurity, Computing, etc).
# Kept in the DB instead of hardcoded so new pathways can be added
# later without touching code or running new migrations.
class Pathway(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# One row = how much ONE criterion matters to ONE pathway.
# Split into its own table (not columns on Pathway) so the engine
# can loop through relevance values dynamically, and so values can
# be tweaked via Django admin after pilot testing without migrations.
class PathwayRelevance(models.Model):
    pathway = models.ForeignKey(Pathway, on_delete=models.CASCADE)
    criterion_name = models.CharField(max_length=50)
    relevance_score = models.FloatField()

    def __str__(self):
        return f"{self.pathway.name} - {self.criterion_name}: {self.relevance_score}"
    



# Stores the engine's computed scores for ONE pathway, for ONE assessment.
# Three rows per assessment (one per pathway) — knowledge_score and
# preference_score are kept separate so the dashboard can show the
# breakdown, not just the final number.
class PathwayScore(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    pathway = models.ForeignKey(Pathway, on_delete=models.CASCADE)
    knowledge_score = models.FloatField()
    preference_score = models.FloatField()
    final_score = models.FloatField()

    def __str__(self):
        return f"{self.pathway.name} - {self.final_score} (Assessment {self.assessment.test_taker_id})"