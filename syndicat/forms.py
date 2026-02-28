from django import forms
from .models import Syndicat, MemberCategory, Member


class SyndicatForm(forms.ModelForm):
    class Meta:
        model = Syndicat
        fields = [
            "nom",
            "nom_complet",
            "pays",
            "description",
            "logo",
            "image_fond",
            "image_fond_verso",
            "cachet",
            "signataire_nom",
            "signataire_titre",
            "signature",
            "clause_legale",
        ]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Ex: Sigle"}),
            "nom_complet": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Nom complet"}),
            "pays": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Ex: RDC"}),
            "description": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 2}),
            "logo": forms.FileInput(attrs={"class": "form-control form-control-sm"}),
            "image_fond": forms.FileInput(attrs={"class": "form-control form-control-sm"}),
            "image_fond_verso": forms.FileInput(attrs={"class": "form-control form-control-sm"}),
            "cachet": forms.FileInput(attrs={"class": "form-control form-control-sm"}),
            "signataire_nom": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "signataire_titre": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "ex: Le Président"}),
            "signature": forms.FileInput(attrs={"class": "form-control form-control-sm"}),
            "clause_legale": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 2}),
        }


class MemberCategoryForm(forms.ModelForm):
    class Meta:
        model = MemberCategory
        fields = ["nom", "ordre"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: Propriétaire"}),
            "ordre": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }


class MemberForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        syndicat = kwargs.pop("syndicat", None)
        super().__init__(*args, **kwargs)
        if syndicat:
            self.fields["categorie"].queryset = syndicat.categories.all()
            self.fields["syndicat"].initial = syndicat
            self.fields["syndicat"].widget = forms.HiddenInput()

    class Meta:
        model = Member
        fields = [
            "syndicat",
            "categorie",
            "numero_membre",
            "prenom",
            "nom",
            "email",
            "telephone",
            "ministere_entreprise",
            "adresse",
            "photo",
            "date_adhesion",
            "actif",
        ]
        widgets = {
            "syndicat": forms.Select(attrs={"class": "form-control"}),
            "categorie": forms.Select(attrs={"class": "form-control"}),
            "numero_membre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Auto si vide"}),
            "prenom": forms.TextInput(attrs={"class": "form-control"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "ministere_entreprise": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: ENVIRONNEMENT"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
            "date_adhesion": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
