from django.db import models
from django.utils import timezone
from decimal import Decimal


class Category(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'
    TYPE_CHOICES = [(INCOME, 'Przychód'), (EXPENSE, 'Wydatek')]

    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    icon = models.CharField(max_length=50, default='bi-tag')
    color = models.CharField(max_length=7, default='#6c757d')

    class Meta:
        ordering = ['name']
        verbose_name = 'Kategoria'
        verbose_name_plural = 'Kategorie'

    def __str__(self):
        return f'{self.name} ({self.get_category_type_display()})'


class Account(models.Model):
    CHECKING = 'checking'
    SAVINGS = 'savings'
    CREDIT = 'credit'
    CASH = 'cash'
    ACCOUNT_TYPES = [
        (CHECKING, 'Konto bieżące'),
        (SAVINGS, 'Oszczędnościowe'),
        (CREDIT, 'Karta kredytowa'),
        (CASH, 'Gotówka'),
    ]

    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default=CHECKING)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='PLN')
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Konto'
        verbose_name_plural = 'Konta'

    def __str__(self):
        return f'{self.name} ({self.currency})'


class Transaction(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'
    TYPE_CHOICES = [(INCOME, 'Przychód'), (EXPENSE, 'Wydatek')]

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    description = models.CharField(max_length=255, blank=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_imported = models.BooleanField(default=False)
    external_id = models.CharField(max_length=200, blank=True, db_index=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Transakcja'
        verbose_name_plural = 'Transakcje'

    def __str__(self):
        sign = '+' if self.transaction_type == self.INCOME else '-'
        return f'{sign}{self.amount} — {self.description or str(self.category)}'


class BankImport(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='imports')
    file_name = models.CharField(max_length=255)
    imported_at = models.DateTimeField(auto_now_add=True)
    records_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-imported_at']
        verbose_name = 'Import bankowy'
        verbose_name_plural = 'Importy bankowe'

    def __str__(self):
        return f'{self.file_name} ({self.imported_at:%Y-%m-%d})'


class LinkedBankAccount(models.Model):
    PENDING = 'pending'
    LINKED = 'linked'
    ERROR = 'error'
    STATUS_CHOICES = [
        (PENDING, 'Oczekuje na autoryzację'),
        (LINKED, 'Połączone'),
        (ERROR, 'Błąd'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='linked_banks')
    institution_id = models.CharField(max_length=100)
    institution_name = models.CharField(max_length=200)
    institution_logo = models.URLField(blank=True)
    requisition_id = models.CharField(max_length=100, unique=True)
    # UUID sent as ?ref= in OAuth callback — lets us look up this record
    reference = models.CharField(max_length=36, unique=True)
    gocardless_account_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    last_synced = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Podlaczone konto'
        verbose_name_plural = 'Podlaczone konta'

    def __str__(self):
        return f'{self.institution_name} → {self.account.name} [{self.get_status_display()}]'
