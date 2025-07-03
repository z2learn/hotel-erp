# forms.py
from django import forms
from .models import MaintenanceWork, Grievance
from django.contrib.auth import get_user_model

User = get_user_model()

class MaintenanceWorkForm(forms.ModelForm):
    class Meta:
        model = MaintenanceWork
        fields = [
            'supervisor_name', 'supervisor_phone', 'worker_name', 'worker_phone',
            'work_description', 'parts_replaced', 'product_name', 'product_cost',
            'labor_charge', 'invoice_image', 'work_status', 'start_time',
            'completion_time', 'remarks'
        ]
        widgets = {
            'supervisor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supervisor name'
            }),
            'supervisor_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supervisor phone number'
            }),
            'worker_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter worker name'
            }),
            'worker_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter worker phone number'
            }),
            'work_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the work performed'
            }),
            'parts_replaced': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List parts that were replaced or fixed'
            }),
            'product_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product name (if any product was replaced)'
            }),
            'product_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'labor_charge': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'invoice_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'work_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'completion_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional remarks or notes'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        completion_time = cleaned_data.get('completion_time')
        work_status = cleaned_data.get('work_status')
        
        # Validate completion time is after start time
        if start_time and completion_time and completion_time <= start_time:
            raise forms.ValidationError("Completion time must be after start time.")
        
        # If work is completed, completion time is required
        if work_status == 'completed' and not completion_time:
            raise forms.ValidationError("Completion time is required when work status is completed.")
        
        return cleaned_data


class GrievanceAssignForm(forms.ModelForm):
    class Meta:
        model = Grievance
        fields = ['assigned_to', 'priority', 'status']
        widgets = {
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users to only maintenance staff
        self.fields['assigned_to'].queryset = User.objects.filter(user_type='maintenance', is_active=True)
        self.fields['assigned_to'].empty_label = "Select maintenance staff"
