from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Booking, Room, CustomUser
from datetime import date, timedelta

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'required': True
        })
    )

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'guest_name', 'guest_email', 'guest_phone', 'room',
            'check_in_date', 'check_out_date', 'number_of_guests',
            'special_requests', 'advance_payment'
        ]
        
        widgets = {
            'guest_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter guest full name',
                'required': True
            }),
            'guest_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address',
                'required': True
            }),
            'guest_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number',
                'required': True,
                'pattern': '[0-9]{10}',
                'title': 'Please enter a valid 10-digit phone number'
            }),
            'room': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
                'id': 'room-select'
            }),
            'check_in_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
                'min': str(date.today())
            }),
            'check_out_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
                'min': str(date.today() + timedelta(days=1))
            }),
            'number_of_guests': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10',
                'required': True
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special requests or notes...'
            }),
            'advance_payment': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'].queryset = Room.objects.filter(is_available=True)
        self.fields['room'].empty_label = "Select a room"
    
    def clean(self):
        cleaned_data = super().clean()
        check_in_date = cleaned_data.get('check_in_date')
        check_out_date = cleaned_data.get('check_out_date')
        room = cleaned_data.get('room')
        number_of_guests = cleaned_data.get('number_of_guests')
        
        # Validate dates
        if check_in_date and check_out_date:
            if check_in_date >= check_out_date:
                raise forms.ValidationError("Check-out date must be after check-in date.")
            
            if check_in_date < date.today():
                raise forms.ValidationError("Check-in date cannot be in the past.")
        
        # Validate guest count against room capacity
        if room and number_of_guests:
            if number_of_guests > room.max_occupancy:
                raise forms.ValidationError(f"Number of guests ({number_of_guests}) exceeds room capacity ({room.max_occupancy}).")
        
        return cleaned_data