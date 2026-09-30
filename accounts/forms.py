import re

from django import forms
from django.contrib.auth import authenticate
from .models import Utilisateur


class InscriptionForm(forms.ModelForm):

    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum 8 caractères',
        })
    )
    password2 = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Répéter le mot de passe',
        })
    )
    accepter_cgu = forms.BooleanField(
        label="J'accepte les conditions d'utilisation",
        required=True,
    )

    class Meta:
        model = Utilisateur
        fields = ['nom', 'prenom', 'email', 'telephone', 'role', 'ville']
        widgets = {
            'nom':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre nom'}),
            'prenom':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Votre prénom'}),
            'email':     forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemple.com'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+237 6XX XXX XXX'}),
            'role':      forms.Select(attrs={'class': 'form-select'}),
            'ville':     forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = [
            ('LOCATAIRE', 'Locataire   Je cherche un logement'),
            ('BAILLEUR',  'Bailleur   Je propose un logement'),
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if Utilisateur.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        if p1 and len(p1) < 8:
            raise forms.ValidationError("Minimum 8 caractères requis.")
        return cleaned
    def clean_nom(self):
        nom = self.cleaned_data.get('nom', '').strip()
        if not nom:
            raise forms.ValidationError("Le nom est obligatoire.")
        if re.search(r'\d', nom):
            raise forms.ValidationError("Le nom ne doit pas contenir de chiffres.")
        if not re.match(r"^[A-Za-zÀ-ÿ\s\-']+$", nom):
            raise forms.ValidationError(
                "Le nom ne doit contenir que des lettres, espaces ou tirets.")
        return nom.title()   # capitalise chaque mot : "jean dupont" → "Jean Dupont"
 
    # ── Validation PRÉNOM : lettres, espaces et tirets uniquement ──
    def clean_prenom(self):
        prenom = self.cleaned_data.get('prenom', '').strip()
        if not prenom:
            raise forms.ValidationError("Le prénom est obligatoire.")
        if re.search(r'\d', prenom):
            raise forms.ValidationError("Le prénom ne doit pas contenir de chiffres.")
        if not re.match(r"^[A-Za-zÀ-ÿ\s\-']+$", prenom):
            raise forms.ValidationError(
                "Le prénom ne doit contenir que des lettres, espaces ou tirets.")
        return prenom.title()
 
    # ── Validation TÉLÉPHONE : +237 suivi de 9 chiffres ──────────
    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone', '').strip()
        if not telephone:
            raise forms.ValidationError("Le numéro de téléphone est obligatoire.")
 
        # Normaliser : retirer les espaces pour la validation
        telephone_clean = telephone.replace(' ', '').replace('-', '')
 
        # Format accepté : +237XXXXXXXXX (13 caractères au total)
        if not re.match(r'^\+237[0-9]{9}$', telephone_clean):
            raise forms.ValidationError(
                "Numéro invalide. Format requis : +237 suivi de 9 chiffres. "
                "Exemple : +237 691234567"
            )
 
        return telephone_clean   # stocker sans espaces
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ConnexionForm(forms.Form):

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.com',
        })
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
        })
    )
    se_souvenir = forms.BooleanField(
        label='Se souvenir de moi',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def clean(self):
        email    = self.cleaned_data.get('email', '').lower()
        password = self.cleaned_data.get('password')
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise forms.ValidationError("Email ou mot de passe incorrect.")
            if not user.is_active:
                raise forms.ValidationError("Compte non activé. Vérifiez votre email.")
            self.cleaned_data['user'] = user
        return self.cleaned_data


class ProfilForm(forms.ModelForm):

    class Meta:
        model = Utilisateur
        fields = [
            'nom', 'prenom', 'telephone', 'genre',
            'date_naissance', 'bio', 'avatar',
            'ville', 'quartier', 'adresse',
            'notifications_email', 'notifications_push', 'mode_sombre'
        ]
        widgets = {
            'nom':            forms.TextInput(attrs={'class': 'form-control'}),
            'prenom':         forms.TextInput(attrs={'class': 'form-control'}),
            'telephone':      forms.TextInput(attrs={'class': 'form-control'}),
            'genre':          forms.Select(attrs={'class': 'form-select'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bio':            forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ville':          forms.TextInput(attrs={'class': 'form-control'}),
            'quartier':       forms.TextInput(attrs={'class': 'form-control'}),
            'adresse':        forms.TextInput(attrs={'class': 'form-control'}),
        }


class ResetPasswordDemandeForm(forms.Form):

    email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre email',
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if not Utilisateur.objects.filter(email=email).exists():
            raise forms.ValidationError("Aucun compte associé à cet email.")
        return email


class ResetPasswordConfirmForm(forms.Form):

    password1 = forms.CharField(
        label='Nouveau mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        if p1 and len(p1) < 8:
            raise forms.ValidationError("Minimum 8 caractères requis.")
        return cleaned
    