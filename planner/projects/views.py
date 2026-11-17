from django.shortcuts import render

# Create your views here.

from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView

from .models import Project

from .serializers import ProjectSerializer,AssignedProjectSerializer,TaskSerializer

from .models import AssignedProject,Task

from rest_framework.views import APIView

from rest_framework.response import Response

from planner.utils import generate_tasks

from django.db import transaction

from planner.pagination import CustomPagination

# from authentication.models import Profile

class ProjectListCreateView(ListCreateAPIView):

    pagination_class=CustomPagination

    queryset=Project.objects.filter(active_status=True)

    serializer_class=ProjectSerializer
class ProjectRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):

    lookup_field='uuid'

    queryset=Project.objects.filter(active_status=True)

    serializer_class=ProjectSerializer

    def perform_destroy(self, instance):
        instance.active_status=False

        instance.save()

class AssignedProjectListCreateView(ListCreateAPIView):
    pagination_class=CustomPagination

    queryset=AssignedProject.objects.filter(active_status=True).select_related('project','coordinator').prefetch_related('developers')

    serializer_class=AssignedProjectSerializer

class AssignedProjectRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):

    lookup_field='uuid'

    queryset=AssignedProject.objects.filter(active_status=True).select_related('project','coordinator').prefetch_related('developers')
    
    serializer_class=AssignedProjectSerializer

    def perform_destroy(self, instance):

        instance.active_status=False

        instance.save()

class TaskListCreateView(ListCreateAPIView):

    pagination_class=CustomPagination

    def get_queryset(self):

        uuid = self.request.query_params.get('project')

        # Task.objects.filter(assigned_project__uuid=uuid)
        
        if uuid:

           assigned_project = AssignedProject.objects.get(uuid=uuid)

        # tasks=assigned_project.task_set.all() reverse look up without realted name

           tasks=assigned_project.assigned_tasks.filter(active_status=True).select_related('assigned_project','assigned_to')

           return tasks
        return Task.objects.none()
    
    serializer_class = TaskSerializer

class TaskRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):

    lookup_field='uuid'

    queryset=Task.objects.filter(active_status=True).select_related('assigned_project','assigned_to')
    
    serializer_class=TaskSerializer

    def perform_destroy(self, instance):

        instance.active_status=False

        instance.save()

class TaskCreateWithAI(APIView):

    def post(self,request,*args,**kwargs):

        uuid=kwargs.get('uuid')

        try:

                assigned_project=AssignedProject.objects.get(uuid=uuid)

                result= generate_tasks(assigned_project)

                tasks=[Task(title=task.title,
                        description=task.description,
                        assigned_project=assigned_project,
                        assigned_to_id=task.developer_id,
                        priority=task.priority) for task in result.tasks]

                with transaction.atomic():

                    Task.objects.bulk_create(tasks)

                    data={'msg':'Tasks assigned successfully'}

                    return Response(data,status=200)

        except Exception as e:
            
            data={'msg':'failed to create tasks'}

            return Response(data,status=400)
            

#f=open('','r')

#
    