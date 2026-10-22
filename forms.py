from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import Company, Job, User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=User.Role.choices)
    company_name = forms.CharField(max_length=160, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "role")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("role") == User.Role.EMPLOYER and not cleaned.get("company_name", "").strip():
            self.add_error("company_name", "Add your company name to create an employer account.")
        return cleaned

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
            if user.role == User.Role.EMPLOYER:
                Company.objects.create(
                    owner=user, name=self.cleaned_data["company_name"].strip()
                )
        return user


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = (
            "title",
            "summary",
            "description",
            "location",
            "employment_type",
            "work_mode",
            "salary_min",
            "salary_max",
            "status",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 7}),
            "summary": forms.TextInput(attrs={"placeholder": "A concise, engaging role summary"}),
        }

    def clean(self):
        cleaned = super().clean()
        low, high = cleaned.get("salary_min"), cleaned.get("salary_max")
        if low is not None and high is not None and low > high:
            self.add_error("salary_max", "Maximum salary must be at least the minimum.")
        return cleaned


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ("name", "website", "industry", "location", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}
