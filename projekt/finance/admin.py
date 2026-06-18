from django.contrib import admin
from .models import Transaction, Category, Account, BankImport, LinkedBankAccount


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'color']
    list_filter = ['category_type']


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_type', 'balance', 'currency', 'bank_name']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'transaction_type', 'amount', 'category', 'account', 'description']
    list_filter = ['transaction_type', 'category', 'account', 'date']
    date_hierarchy = 'date'
    search_fields = ['description']


@admin.register(BankImport)
class BankImportAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'account', 'imported_at', 'records_count']
    readonly_fields = ['imported_at']


@admin.register(LinkedBankAccount)
class LinkedBankAccountAdmin(admin.ModelAdmin):
    list_display = ['institution_name', 'account', 'status', 'last_synced', 'created_at']
    list_filter = ['status']
    readonly_fields = ['requisition_id', 'reference', 'gocardless_account_id', 'created_at', 'last_synced']
