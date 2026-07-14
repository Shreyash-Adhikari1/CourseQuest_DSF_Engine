from django.db import models

# Create your models here.

# The Assessment Table Stores the Raw Payload we receive from the VR.
class Assessment(models.Model):
    test_taker_id=models.IntegerField()
    session_id= models.CharField(max_length=100)
    assessment_version= models.CharField(max_length=20)
    raw_payload=models.JSONField()
    submitted_at= models.DateTimeField(auto_now_add=True)

    # optional identity fields — filled in after assessment
    test_taker_name = models.CharField(max_length=100, blank=True)
    test_taker_email = models.EmailField(blank=True)

    def __str__(self):
        return f"Assessment {self.test_taker_id}-{self.session_id}"
    
# The Criterion Score Table, It saves the "values" & "confidence" scores per criterion
# We make a separate table to store CriterionScores because 
# we need to multiply the scores with different sets of pathway_relevances
# Cramming it all up in the Assessment would make it a query hell
# With a separate table, we can just use a loop to get all six criterion scores

class CriterionScore(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    criterion_name = models.CharField(max_length=50)
    value = models.FloatField()
    confidence = models.FloatField()

    def __str__(self):
        return f"{self.criterion_name} - Assessment {self.assessment.test_taker_id}"