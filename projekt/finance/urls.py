from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/<int:pk>/edit/', views.edit_transaction, name='edit_transaction'),
    path('transactions/<int:pk>/delete/', views.delete_transaction, name='delete_transaction'),
    path('categories/', views.categories, name='categories'),
    path('categories/<int:pk>/delete/', views.delete_category, name='delete_category'),
    path('accounts/', views.accounts, name='accounts'),
    path('accounts/<int:pk>/delete/', views.delete_account, name='delete_account'),
    path('reports/', views.reports, name='reports'),
    path('reports/chart-data/', views.reports_chart_data, name='reports_chart_data'),
    path('banking/', views.banking, name='banking'),
    path('banking/institutions/', views.banking_institutions, name='banking_institutions'),
    path('banking/link/', views.banking_link_start, name='banking_link_start'),
    path('banking/callback/', views.banking_callback, name='banking_callback'),
    path('banking/<int:pk>/sync/', views.banking_sync, name='banking_sync'),
    path('banking/<int:pk>/unlink/', views.banking_unlink, name='banking_unlink'),
]