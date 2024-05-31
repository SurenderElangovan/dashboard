import os
import uuid
import json
import shutil
import base64
import traceback
from datetime import datetime

from django.core.files.storage import default_storage
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import ProjectMaster
from .serializers import ProjectMasterCreateOrUpdateOrGetSerializer, ProjectMasterGetListSerializer

HTML_FOLDER = r'FILE_DB\FileContainer'
DATA_FOLDER = r'FILE_DB\DataContainer'
HTML_ALLOWED_EXTENSIONS = ['html', 'htm']

if not os.path.exists(HTML_FOLDER):
    os.makedirs(HTML_FOLDER)

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def html_allowed_file(filename):
    """
    Check if the filename has an allowed HTML extension.

    Args:
    filename (str): The name of the file to be checked.

    Returns:
    bool: True if the file has an allowed HTML extension, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in HTML_ALLOWED_EXTENSIONS

def generate_sub_folder():
    """
    Generate a unique subfolder name that does not already exist in HTML_FOLDER or DATA_FOLDER.

    Returns:
    str: A unique subfolder name generated using UUID.
    """
    while True:
        subfolder_name = uuid.uuid4().hex
        html_subfolder_path = os.path.join(HTML_FOLDER, subfolder_name)
        data_subfolder_path = os.path.join(DATA_FOLDER, subfolder_name)
        
        if not os.path.exists(html_subfolder_path) and not os.path.exists(data_subfolder_path):
            return subfolder_name

def remove_subfolder(file_path):
    """
    Remove the subfolder containing the given file.

    Args:
    file_path (str): The path of the file whose containing subfolder needs to be removed.
    """
    try:
        directory_path, _ = os.path.split(file_path)
        shutil.rmtree(directory_path)
    except:
        pass

class ProjectCreateOrUploadView(APIView):
    """
    API endpoint for creating or uploading a project.
    """
    def post(self, request):
        """
        Handle POST request for creating or uploading a project.

        Args:
        request (Request): The request object containing project data.

        Returns:
        Response: Response indicating the success or failure of the operation.
        """
        if 'html_file' not in request.FILES:
            return Response({'message': 'Html File required.'}, status=status.HTTP_400_BAD_REQUEST)
        if 'name' not in request.data or 'description' not in request.data:
            return Response({'message': 'Name and Description required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        html_file = request.FILES['html_file']
        data_file = request.FILES.get('data_file', None)
        name = request.data['name']
        description = request.data.get('description')
        chart_type = request.data.get('chart_type')
        sub_chart_type = request.data.get('sub_chart_type')
        project_id = request.data.get('id', None)
        project_status = request.data.get('project_status', "Draft")
        selected_column = request.data.get('selected_column', '[]')

        if html_file and html_allowed_file(html_file.name):
            subfolder_name = generate_sub_folder()
            html_filename = html_file.name
            data_filename = data_file.name if data_file else None

            html_file_path = os.path.join(HTML_FOLDER, subfolder_name, html_filename)
            os.makedirs(os.path.join(HTML_FOLDER, subfolder_name),exist_ok=True)
            with default_storage.open(html_file_path, 'wb+') as destination:
                for chunk in html_file.chunks():
                    destination.write(chunk)

            data_file_path = None
            if data_filename:
                data_file_path = os.path.join(DATA_FOLDER, subfolder_name, data_filename)
                os.makedirs(os.path.join(DATA_FOLDER, subfolder_name),exist_ok=True)
                with default_storage.open(data_file_path, 'wb+') as destination:
                    for chunk in data_file.chunks():
                        destination.write(chunk)

            modified_date = datetime.utcnow()

            serializer_data = {
                'name': name,
                'description': description,
                'chart_type':chart_type,
                'sub_chart_type':sub_chart_type,
                'html_file_path': html_file_path,
                'data_file_path': data_file_path,
                'modified_date': modified_date,
                'project_status': project_status,
                'selected_column': selected_column
            }

            try:
                if project_id:
                    metadata = ProjectMaster.objects.get(id=project_id)
                    old_html_filepath = metadata.html_file_path
                    old_data_filepath = metadata.data_file_path
                    remove_subfolder(old_html_filepath)
                    remove_subfolder(old_data_filepath)
                    serializer = ProjectMasterCreateOrUpdateOrGetSerializer(metadata, data=serializer_data)
                else:
                    serializer = ProjectMasterCreateOrUpdateOrGetSerializer(data=serializer_data)
                if project_status in ["Published","Draft"]:
                    if serializer.is_valid():
                        new_metadata = serializer.save()
                        if project_status == "Published":
                            embed_url = f"/dashboard/view/embed?hash_code={new_metadata.hash_code}"
                            return Response({'message': 'File uploaded successfully.', 'embed_url': embed_url}, status=status.HTTP_201_CREATED)
                        elif project_status == "Draft":
                            return Response({'message': 'File saved successfully.'}, status=status.HTTP_200_OK)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'message': "Project_status can only ['Published','Draft']"},status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({'message': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'Invalid file format.'}, status=status.HTTP_400_BAD_REQUEST)

class ProjectGetListView(APIView):
    """
    API endpoint for getting a list of projects.
    """
    def get(self, request):
        """
        Handle GET request for getting a list of projects.

        Args:
        request (Request): The request object.

        Returns:
        Response: Response containing a list of projects or an error message.
        """
        try:
            projects = ProjectMaster.objects.all()
            serializer = ProjectMasterGetListSerializer(projects, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
                return Response({'message': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProjectGetView(APIView):
    """
    API endpoint for getting details of a specific project.
    """
    def get(self, request):
        """
        Handle GET request for getting details of a specific project.

        Args:
        request (Request): The request object containing project ID.

        Returns:
        Response: Response containing project details or an error message.
        """
        try:
            project_id = request.query_params.get("id")
            if project_id:
                project = ProjectMaster.objects.get(id=project_id)
                serializer = ProjectMasterCreateOrUpdateOrGetSerializer(project)
                result = serializer.data
                result['selected_column'] = json.loads(result['selected_column'])
                response_data = {
                    'project_data': result,
                    'html_file': None,
                    'data_file': None
                }
                html_file_path = result.pop('html_file_path')
                data_file_path = result.pop('data_file_path')

                if html_file_path and os.path.isfile(html_file_path):
                    with open(html_file_path, 'rb') as html_file:
                        response_data['html_file'] = base64.b64encode(html_file.read()).decode('utf-8')
                if data_file_path and os.path.isfile(data_file_path):
                    with open(data_file_path, 'rb') as data_file:
                        response_data['data_file'] = base64.b64encode(data_file.read()).decode('utf-8')
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Missing id in query parameter.'}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'message': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
                return Response({'message': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProjectDeleteView(APIView):
    """
    API endpoint for deleting a project.
    """
    def get(self,request):
        """
        Handle GET request for deleting a project.

        Args:
        request (Request): The request object containing project ID.

        Returns:
        Response: Response indicating the success or failure of the deletion operation.
        """
        try:
            project_id = request.query_params.get("id")
            if project_id:
                project = ProjectMaster.objects.get(id=project_id)
                project.delete()
                return Response({'message': 'Project was successfully deleted.'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Missing id in query parameter.'}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'message': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
                return Response({'message': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmbedCodeView(APIView):
    def get(self,request):
        try:
            hash_code = request.query_params.get("hash_code")
            if hash_code:
                project_details = ProjectMaster.objects.get(hash_code=hash_code)
                html_file_path = project_details.html_file_path
                with open(html_file_path, 'r') as file:
                    file_content = file.read()
                return HttpResponse(file_content, content_type='text/html')
        except ObjectDoesNotExist:
            return Response({'message': 'not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
                return Response({'message': f'An error occurred: {traceback.format_exc()}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

