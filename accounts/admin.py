from django.contrib import admin

# Register your models here.from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, LogActivite


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display  = ['email', 'nom', 'prenom', 'role', 'ville', 'is_active', 'date_inscription']
    list_filter   = ['role', 'is_active', 'is_verified', 'is_premium']
    search_fields = ['email', 'nom', 'prenom', 'telephone']
    ordering      = ['-date_inscription']

    fieldsets = (
        ('Identité',     {'fields': ('email', 'password', 'nom', 'prenom', 'telephone', 'avatar')}),
        ('Localisation', {'fields': ('ville', 'quartier', 'adresse')}),
        ('Rôle & Statut',{'fields': ('role', 'is_active', 'is_staff', 'is_verified', 'is_premium')}),
        ('Permissions',  {'fields': ('groups', 'user_permissions')}),
        ('Dates',        {'fields': ('date_inscription',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nom', 'prenom', 'role', 'password1', 'password2'),
        }),
    )
    readonly_fields = ['date_inscription', 'uuid']


@admin.register(LogActivite)
class LogActiviteAdmin(admin.ModelAdmin):
    list_display    = ['utilisateur', 'action', 'succes', 'ip_address', 'cree_le']
    list_filter     = ['action', 'succes']
    search_fields   = ['utilisateur__email']
    readonly_fields = ['utilisateur', 'action', 'ip_address', 'cree_le']
