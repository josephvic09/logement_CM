from django import forms
from .models import Logement, Avis, Reservation, Ville, Quartier


class RechercheForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Quartier, ville, type de logement...',
        })
    )
    ville = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ville',
        })
    )
    quartier = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Quartier',
        })
    )
    type_logement = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous types')] + Logement.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    type_offre = forms.ChoiceField(
        required=False,
        choices=[('', 'Location / Vente')] + Logement.OFFRE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    prix_min = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prix min (FCFA)',
        })
    )
    prix_max = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prix max (FCFA)',
        })
    )
    nb_chambres = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Chambres min',
        })
    )
    standing = forms.ChoiceField(
        required=False,
        choices=[('', 'Tout standing')] + Logement.STANDING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    wifi          = forms.BooleanField(required=False)
    parking       = forms.BooleanField(required=False)
    climatisation = forms.BooleanField(required=False)
    gardien       = forms.BooleanField(required=False)
    piscine       = forms.BooleanField(required=False)
    generateur    = forms.BooleanField(required=False)


class LogementForm(forms.ModelForm):

    class Meta:
        model  = Logement
        fields = [
            'titre', 'description',
            'type_logement', 'type_offre', 'standing', 'meuble',
            'ville', 'quartier', 'adresse', 'latitude', 'longitude',
            'surface', 'nb_chambres', 'nb_salles_bain', 'nb_toilettes', 'etage',
            'prix', 'prix_negociable', 'charges', 'caution',
            'eau_courante', 'electricite', 'internet', 'climatisation',
            'parking', 'gardien', 'generateur', 'piscine',
            'cuisine_equipee', 'balcon', 'securite',
            'disponible', 'date_disponibilite',
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Bel appartement F3 meublé à Bastos Yaoundé',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Décrivez votre logement : état, environnement, points forts, accès...',
            }),
            'type_logement':    forms.Select(attrs={'class': 'form-select'}),
            'type_offre':       forms.Select(attrs={'class': 'form-select'}),
            'standing':         forms.Select(attrs={'class': 'form-select'}),
            'meuble':           forms.Select(attrs={'class': 'form-select'}),
            'ville':            forms.Select(attrs={'class': 'form-select', 'id': 'id_ville'}),
            'quartier':         forms.Select(attrs={'class': 'form-select', 'id': 'id_quartier'}),
            'adresse':          forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Rue Bastos, en face du supermarché',
            }),
            'surface':          forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'm²'}),
            'nb_chambres':      forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'nb_salles_bain':   forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'nb_toilettes':     forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'etage':            forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'prix':             forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Montant en FCFA',
            }),
            'charges':          forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'FCFA'}),
            'caution':          forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'FCFA'}),
            'date_disponibilite': forms.DateInput(attrs={
                'class': 'form-control',
                'type':  'date',
            }),
            'latitude':  forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Rendre certains champs obligatoires
        self.fields['titre'].required          = True
        self.fields['description'].required    = True
        self.fields['type_logement'].required  = True
        self.fields['type_offre'].required     = True
        self.fields['ville'].required          = True
        self.fields['adresse'].required        = True
        self.fields['prix'].required           = True
        self.fields['nb_chambres'].required    = True

        # Champs optionnels
        self.fields['quartier'].required          = False
        self.fields['surface'].required           = False
        self.fields['charges'].required           = False
        self.fields['caution'].required           = False
        self.fields['date_disponibilite'].required = False

        # Quartiers vides par défaut
        self.fields['quartier'].queryset = Quartier.objects.none()

        # Si ville déjà sélectionnée (edit)
        if 'ville' in self.data:
            try:
                ville_id = int(self.data.get('ville'))
                self.fields['quartier'].queryset = Quartier.objects.filter(
                    ville_id=ville_id
                ).order_by('nom')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.ville:
            self.fields['quartier'].queryset = Quartier.objects.filter(
                ville=self.instance.ville
            ).order_by('nom')

    def clean_prix(self):
        prix = self.cleaned_data.get('prix')
        if prix and prix <= 0:
            raise forms.ValidationError("Le prix doit être supérieur à 0.")
        return prix

    def clean_nb_chambres(self):
        nb = self.cleaned_data.get('nb_chambres')
        if nb and nb <= 0:
            raise forms.ValidationError("Le nombre de chambres doit être au moins 1.")
        return nb


class AvisForm(forms.ModelForm):
    class Meta:
        model  = Avis
        fields = ['note', 'commentaire']
        widgets = {
            'note': forms.RadioSelect(
                choices=[(i, f'{i} ⭐') for i in range(1, 6)]
            ),
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows':  3,
                'placeholder': 'Partagez votre expérience...',
            }),
        }


class ReservationForm(forms.ModelForm):
    class Meta:
        model  = Reservation
        fields = ['type_demande', 'date_debut', 'date_fin', 'message']
        widgets = {
            'type_demande': forms.Select(attrs={'class': 'form-select'}),
            'date_debut':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin':     forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'message':      forms.Textarea(attrs={
                'class': 'form-control',
                'rows':  3,
                'placeholder': 'Message au bailleur (optionnel)',
            }),
        }