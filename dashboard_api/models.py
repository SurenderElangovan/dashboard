import uuid
import hashlib
from django.db import models

def generate_hash_code():
    """
    Generate a unique hash code using SHA-256 algorithm and UUID.
    Ensures the hash code is not already in the ProjectMaster model.

    Returns:
    str: A unique hash code.
    """
    while True:
        hash_code = hashlib.sha256(uuid.uuid4().hex.encode()).hexdigest()
        if not ProjectMaster.objects.filter(hash_code=hash_code).exists():
            return hash_code

class ProjectMaster(models.Model):
    """
    Model representing a project.

    Attributes:
    name (str): The name of the project.
    description (str): The description of the project.
    chart_type (str): The chart type of the project.
    sub_chart_type (str): The sub chart type of the project.
    html_file_path (str): The path to the HTML file associated with the project.
    data_file_path (str): The path to the data file associated with the project (optional).
    project_status (str): The status of the project (e.g., "Draft", "Published").
    selected_column (list): The selected columns for the project (JSON format).
    hash_code (str): The unique hash code generated for the project.
    created_date (DateTime): The date and time when the project was created.
    modified_date (DateTime): The date and time when the project was last modified.
    is_active (bool): Indicates whether the project is active or not.

    """
    name = models.CharField(max_length=120, null=False)
    description = models.CharField(max_length=200, null=True)
    chart_type = models.CharField(max_length=200, null=True)
    sub_chart_type = models.CharField(max_length=200, null=True)
    html_file_path = models.CharField(max_length=200, null=False)
    data_file_path = models.CharField(max_length=200, null=True, blank=True)
    project_status = models.CharField(max_length=20, default="Draft")
    selected_column = models.JSONField(null=True, blank=True)
    hash_code = models.CharField(max_length=64, unique=True, default=generate_hash_code)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """
        Return a string representation of the project.

        Returns:
        str: The name of the project.
        """
        return self.name
