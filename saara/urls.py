"""
URL configuration for saara project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from saara.authapp import views
from saara.erp import views
router = routers.DefaultRouter()
router.register(r"erp/dept", views.DepartmentViewSet)
router.register(r"erp/stud-fees", views.StudentFeesViewSet)
router.register(r"erp/teacher", views.TeacherViewSet)
router.register(r"erp/assignment-sub", views.AssignmentSubmissionViewSet)
router.register(r"erp/assignment", views.AssignmentViewSet)
router.register(r"erp/result", views.ResultViewSet)
router.register(r"erp/attendance", views.AttendanceViewSet)
router.register(r"erp/admin", views.AdminViewSet)
router.register(r"erp/course", views.CourseViewSet)
router.register(r"erp/course-faculty", views.CourseFacultyViewSet)
# router.register(r"erp", views.)
# router.register(r"groups", views.GroupViewSet)
urlpatterns = [
    path("", include(router.urls)),
    path('admin/', admin.site.urls),
    path('api/', include('saara.authapp.urls')),
    path('erp/', include('saara.erp.urls'))
]