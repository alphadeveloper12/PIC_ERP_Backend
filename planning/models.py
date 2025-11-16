from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return f"{self.project.name} → {self.name}"


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('category', 'name')

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class Activity(models.Model):
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name="activities")
    activity_id = models.CharField(max_length=100)
    activity_name = models.CharField(max_length=255, null=True, blank=True)
    original_duration = models.FloatField(null=True, blank=True)
    early_start = models.DateField(null=True, blank=True)
    early_finish = models.DateField(null=True, blank=True)
    late_start = models.DateField(null=True, blank=True)
    late_finish = models.DateField(null=True, blank=True)
    total_float = models.FloatField(null=True, blank=True)
    budgeted_total_cost = models.FloatField(null=True, blank=True)
    owner = models.CharField(max_length=255, null=True, blank=True)
    activity_location = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.activity_id