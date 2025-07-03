from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Room, WorkerProfile

class WorkerCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    # Worker-specific fields
    employee_id = forms.CharField(max_length=20, required=True)
    specialization = forms.CharField(max_length=100, required=True, 
                                   help_text="e.g., Plumbing, Electrical, HVAC, General Maintenance")
    experience_years = forms.IntegerField(min_value=0, initial=0)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'first_name', 'last_name', 
                 'password1', 'password2', 'employee_id', 'specialization', 'experience_years')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes for styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Add placeholders
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['email'].widget.attrs['placeholder'] = 'Email address'
        self.fields['phone_number'].widget.attrs['placeholder'] = '+1234567890'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last Name'
        self.fields['employee_id'].widget.attrs['placeholder'] = 'Employee ID'
        self.fields['specialization'].widget.attrs['placeholder'] = 'Specialization'
        self.fields['experience_years'].widget.attrs['placeholder'] = 'Years of experience'
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id']
        if WorkerProfile.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError("Employee ID already exists.")
        return employee_id
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email address already exists.")
        return email

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'room_type', 'price_per_night', 'max_occupancy', 'amenities']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 101'}),
            'room_type': forms.Select(attrs={'class': 'form-control'}),
            'price_per_night': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'max_occupancy': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': '2'}),
            'amenities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List room amenities...'}),
        }
    
    def clean_room_number(self):
        room_number = self.cleaned_data['room_number']
        if self.instance.pk is None:  # Only check for new rooms
            if Room.objects.filter(room_number=room_number).exists():
                raise forms.ValidationError("Room number already exists.")
        return room_number

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class MaintenanceAssignmentForm(forms.Form):
    worker = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='MAINTENANCE'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select a worker..."
    )
    supervisor_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supervisor Name'})
    )
    supervisor_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supervisor Phone'})
    )
    priority = forms.ChoiceField(
        choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('URGENT', 'Urgent')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes...'})
    )