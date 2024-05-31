from rest_framework import serializers
from .models import ProjectMaster

class ProjectMasterCreateOrUpdateOrGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMaster
        fields = ['id', 'name', 'description', 'chart_type','sub_chart_type','html_file_path', 'data_file_path', 'project_status', 'selected_column', 'modified_date']

class ProjectMasterGetListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMaster
        fields = ['id','name', 'description','chart_type','sub_chart_type','project_status','modified_date']