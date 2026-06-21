from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Transaction, Category, Account

_CURRENT_YEAR = timezone.now().year


class TransactionForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now,
    )

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'category', 'account', 'description', 'date']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_transaction_type'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select', 'id': 'id_category'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opis transakcji...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].required = False
        self.fields['category'].empty_label = '— Brak kategorii —'
        self.fields['account'].queryset = Account.objects.all()

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError('Kwota musi być większa od zera.')
        return amount

    def clean_date(self):
        d = self.cleaned_data.get('date')
        if d and d.year < 1900:
            raise ValidationError('Data jest nieprawidłowa.')
        if d and d.year > _CURRENT_YEAR + 10:
            raise ValidationError('Data jest zbyt odległa w przyszłości.')
        return d


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category_type': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError('Nazwa kategorii nie może być pusta.')
        return name


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'account_type', 'balance', 'currency', 'bank_name', 'account_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_currency(self):
        currency = self.cleaned_data.get('currency', '').strip().upper()
        if not currency:
            return 'PLN'
        if len(currency) != 3 or not currency.isalpha():
            raise ValidationError('Waluta musi być 3-literowym kodem ISO (np. PLN, EUR, USD).')
        return currency

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError('Nazwa konta nie może być pusta.')
        return name


class PlaidImportForm(forms.Form):
    account = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        label='Konto docelowe',
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={'required': 'Wybierz konto docelowe.'},
    )


class BankImportForm(forms.Form):
    account = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        label='Konto',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    csv_file = forms.FileField(
        label='Plik CSV',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv,.txt'}),
    )

    def clean_csv_file(self):
        f = self.cleaned_data.get('csv_file')
        if f:
            name = f.name.lower()
            if not (name.endswith('.csv') or name.endswith('.txt')):
                raise ValidationError('Dozwolone są tylko pliki .csv lub .txt.')
            if f.size > 10 * 1024 * 1024:  # 10 MB limit
                raise ValidationError('Plik jest zbyt duży. Maksymalny rozmiar to 10 MB.')
        return f


class ReportFilterForm(forms.Form):
    MONTHS = [
        ('', 'Cały rok'),
        ('1', 'Styczeń'), ('2', 'Luty'), ('3', 'Marzec'),
        ('4', 'Kwiecień'), ('5', 'Maj'), ('6', 'Czerwiec'),
        ('7', 'Lipiec'), ('8', 'Sierpień'), ('9', 'Wrzesień'),
        ('10', 'Październik'), ('11', 'Listopad'), ('12', 'Grudzień'),
    ]
    year = forms.IntegerField(
        initial=_CURRENT_YEAR,
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '2000', 'max': '2100'}),
        error_messages={
            'min_value': 'Rok nie może być wcześniejszy niż 2000.',
            'max_value': 'Rok nie może być późniejszy niż 2100.',
            'invalid': 'Podaj prawidłowy rok (np. 2024).',
        },
    )
    month = forms.ChoiceField(
        choices=MONTHS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class TransactionFilterForm(forms.Form):
    transaction_type = forms.ChoiceField(
        choices=[('', 'Wszystkie'), ('income', 'Przychody'), ('expense', 'Wydatki')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='Wszystkie kategorie',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    account = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        required=False,
        empty_label='Wszystkie konta',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )

    def clean(self):
        cleaned = super().clean()
        date_from = cleaned.get('date_from')
        date_to = cleaned.get('date_to')
        if date_from and date_to and date_from > date_to:
            raise ValidationError('"Data od" nie może być późniejsza niż "Data do".')
        return cleaned