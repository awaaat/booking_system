from django import forms
from users.models.appuser import CustomUser

class RegistrationForm(forms.ModelForm):
    """Form for user registration with password confirmation"""
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confim_password')
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email',
            'phone_number', 'user_role', 'bio', 
            'profile_image', 'password'
        ]
        
    def clean(self):
        """Validate password match and other fields"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
            
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

class ProfileForm(forms.ModelForm):
    """
    Form for editing user profile
    """
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 
                'phone_number', 'bio', 'profile_image'] 