# src/movie/forms.py
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django import forms

class MovieRatingForm(forms.Form):
    rating = forms.IntegerField(
        min_value=1,
        max_value=10,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": "1",
            "max": "10",
            "step": "1",
            "inputmode": "numeric",
            "placeholder": "1–10",
        }),
        help_text="Rate from 1 to 10",
    )


class MovieCommentForm(forms.Form):
    body = forms.CharField(
        max_length=1000,
        required=True,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": "3",
            "placeholder": "Write a comment…",
        }),
    )