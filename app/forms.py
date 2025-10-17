from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(label="Họ và tên", max_length=100, widget=forms.TextInput(attrs={
        "class": "form-control", "placeholder": "Nhập họ và tên"
    }))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={
        "class": "form-control", "placeholder": "Nhập email"
    }))
    subject = forms.CharField(label="Tiêu đề", max_length=200, widget=forms.TextInput(attrs={
        "class": "form-control", "placeholder": "Nhập tiêu đề"
    }))
    message = forms.CharField(label="Nội dung", widget=forms.Textarea(attrs={
        "class": "form-control", "rows": 5, "placeholder": "Nhập nội dung"
    }))


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Customer

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            # tạo Customer kèm theo
            Customer.objects.create(
                user=user,
                name=user.username,
                email=user.email,
                # nhớ thêm field phone trong Customer model
                phone=self.cleaned_data["phone"]
            )
        return user
