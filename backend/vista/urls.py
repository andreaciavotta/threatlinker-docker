from django.urls import path
from vista import views  # Assicurati che il modulo esista e sia corretto

app_name = 'vista' 

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/start/', views.start_task, name='start_task'),
    path('tasks/', views.tasks_list, name='tasks_list'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/<str:cve_id>/', views.single_correlation_detail, name='single_correlation_detail'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),  # URL per eliminare una task
    path('task/<int:task_id>/export/', views.export_task_excel, name='export_task_excel'),
    path('view/cve/<str:cve_id>/', views.view_cve, name='view_cve'),
    path('view/capec/<str:capec_id>/', views.view_capec, name='view_capec'),
    path('view/error/', views.view_error_page, name='view_error'),
    path('stats/', views.database_stats_view, name="database_stats"),
]
