from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Ride, Office


class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        ('passenger', 'Пассажир'),
        ('driver', 'Водитель'),
    ]

    first_name = forms.CharField(max_length=100, label='Имя', required=True)
    last_name = forms.CharField(max_length=100, label='Фамилия', required=True)
    email = forms.EmailField(label='Email', required=True)
    phone = forms.CharField(max_length=20, label='Телефон', required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Роль', widget=forms.RadioSelect)
    city = forms.CharField(max_length=100, label='Ваш город', required=False,
                           help_text='Например: Москва, Санкт-Петербург')
    home_address = forms.CharField(max_length=255, label='Домашний адрес', required=False)
    home_lat = forms.FloatField(widget=forms.HiddenInput(), required=False)
    home_lon = forms.FloatField(widget=forms.HiddenInput(), required=False)

    car_model = forms.CharField(max_length=100, label='Модель автомобиля', required=False)
    car_plate = forms.CharField(max_length=20, label='Гос. номер', required=False)
    car_seats = forms.IntegerField(min_value=1, max_value=8, initial=3,
                                   label='Количество мест для пассажиров', required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs['class'] = 'form-control'
        self.fields['role'].widget.attrs['class'] = ''


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, label='Имя', required=False)
    last_name = forms.CharField(max_length=100, label='Фамилия', required=False)
    email = forms.EmailField(label='Email', required=False)

    class Meta:
        model = UserProfile
        fields = ['phone', 'avatar', 'city', 'home_address', 'home_lat', 'home_lon',
                  'car_model', 'car_plate', 'car_seats']
        widgets = {
            'home_lat': forms.HiddenInput(),
            'home_lon': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class RideCreateForm(forms.ModelForm):
    class Meta:
        model = Ride
        fields = ['office', 'departure_address', 'departure_lat', 'departure_lon',
                  'departure_city', 'departure_time', 'available_seats', 'comment']
        widgets = {
            'departure_lat': forms.HiddenInput(),
            'departure_lon': forms.HiddenInput(),
            'departure_city': forms.HiddenInput(),
            'departure_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'office': forms.Select(attrs={'class': 'form-select'}),
            'departure_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите адрес отправления',
                'id': 'departure_address'
            }),
            'available_seats': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '1', 'max': '8'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 'rows': '3',
                'placeholder': 'Дополнительная информация...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['office'].queryset = Office.objects.filter(is_active=True)
        self.fields['departure_lat'].required = False
        self.fields['departure_lon'].required = False
        self.fields['departure_city'].required = False
        self.fields['available_seats'].initial = 3


class OfficeForm(forms.ModelForm):
    class Meta:
        model = Office
        fields = ['name', 'address', 'city', 'lat', 'lon', 'description', 'photo', 'is_active']
        widgets = {
            'lat': forms.HiddenInput(),
            'lon': forms.HiddenInput(),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class JoinRideForm(forms.Form):
    pickup_address = forms.CharField(
        max_length=500,
        label='Адрес подбора',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Оставьте пустым чтобы использовать адрес отправления',
            'id': 'pickup_address_input'
        })
    )
    pickup_lat = forms.FloatField(widget=forms.HiddenInput(), required=False)
    pickup_lon = forms.FloatField(widget=forms.HiddenInput(), required=False)


class RideFilterForm(forms.Form):
    office = forms.ModelChoiceField(
        queryset=Office.objects.filter(is_active=True),
        required=False,
        empty_label='Все офисы',
        label='Офис',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        label='Город отправления',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город'})
    )
    date = forms.DateField(
        required=False,
        label='Дата',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
