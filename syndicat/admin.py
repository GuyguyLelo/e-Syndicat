from django.contrib import admin
from .models import Syndicat, MemberCategory, Member, Banque


class MemberCategoryInline(admin.TabularInline):
    model = MemberCategory
    extra = 1


@admin.register(Syndicat)
class SyndicatAdmin(admin.ModelAdmin):
    list_display = ["nom", "nom_complet", "signataire_nom", "signataire_titre", "created_at"]
    search_fields = ["nom", "nom_complet"]
    inlines = [MemberCategoryInline]
    fieldsets = (
        (None, {"fields": ("nom", "nom_complet", "pays", "description")}),
        ("Identité visuelle", {"fields": ("logo", "cachet")}),
        ("Signataire (RECTO carte)", {"fields": ("signataire_nom", "signataire_titre", "signature")}),
        ("VERSO carte", {"fields": ("clause_legale",)}),
    )


@admin.register(Banque)
class BanqueAdmin(admin.ModelAdmin):
    list_display = ["nom"]
    search_fields = ["nom"]


@admin.register(MemberCategory)
class MemberCategoryAdmin(admin.ModelAdmin):
    list_display = ["nom", "syndicat", "ordre"]
    list_filter = ["syndicat"]
    ordering = ["syndicat", "ordre", "nom"]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ["nom_complet", "syndicat", "categorie", "numero_membre", "ministere_entreprise", "service", "banque", "matricule", "actif", "date_adhesion"]
    list_filter = ["syndicat", "categorie", "actif"]
    search_fields = ["prenom", "nom", "numero_membre", "email"]
    raw_id_fields = ["syndicat", "categorie"]
    date_hierarchy = "date_adhesion"
