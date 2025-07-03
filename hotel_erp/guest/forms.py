from django import forms
from .models import Grievance

class GrievanceForm(forms.ModelForm):
    class Meta:
        model = Grievance
        fields = ['problem_type', 'detailed_description', 'attachment']
        
        widgets = {
            'problem_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'detailed_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Please describe your problem in detail...',
                'required': True
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'help_text': 'Maximum file size: 2MB (JPG, PNG, GIF only)'
            })
        }
        
        labels = {
            'problem_type': 'Type of Problem',
            'detailed_description': 'Detailed Description',
            'attachment': 'Attachment (Optional)'
        }
    
    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        
        if attachment:
            # Check file size (2MB max)
            if attachment.size > 2 * 1024 * 1024:
                raise forms.ValidationError('File size should not exceed 2MB.')
            
            # Check file extension
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            extension = attachment.name.split('.')[-1].lower()
            
            if extension not in allowed_extensions:
                raise forms.ValidationError('Only JPG, PNG, and GIF files are allowed.')
        
        return attachment
    
    def clean_detailed_description(self):
        description = self.cleaned_data.get('detailed_description')
        
        if description and len(description.strip()) < 10:
            raise forms.ValidationError('Please provide a detailed description (at least 10 characters).')
        
        return description.strip() if description else description