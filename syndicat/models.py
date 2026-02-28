from django.db import models


class Syndicat(models.Model):
    """Syndicat (association). Carte de membre RECTO/VERSO."""
    nom = models.CharField("Nom court / Sigle", max_length=200, help_text="Ex: Sigle du syndicat")
    nom_complet = models.CharField(
        "Nom complet du syndicat",
        max_length=400,
        blank=True,
        help_text="Ex: Syndicat Général Administratif...",
    )
    pays = models.CharField(
        "Pays (pour le VERSO)",
        max_length=200,
        default="République Démocratique du Congo",
        blank=True,
    )
    description = models.TextField(blank=True)
    logo = models.ImageField("Logo", upload_to="syndicats/logos/", blank=True, null=True)
    image_fond = models.ImageField(
        "Image de fond (carte RECTO)",
        upload_to="syndicats/fonds/",
        blank=True,
        null=True,
        help_text="Image de fond pour le RECTO de la carte. Format clair recommandé pour l'impression.",
    )
    image_fond_verso = models.ImageField(
        "Image de fond (carte VERSO)",
        upload_to="syndicats/fonds/",
        blank=True,
        null=True,
        help_text="Image de fond pour le VERSO de la carte. Format clair recommandé pour l'impression.",
    )
    cachet = models.ImageField(
        "Cachet / Sceau (cercle)",
        upload_to="syndicats/cachets/",
        blank=True,
        null=True,
        help_text="Cachet circulaire. Format PNG recommandé (superposé à la signature sur la carte).",
    )
    # Signataire pour les cartes de membre (RECTO)
    signataire_nom = models.CharField("Nom du signataire", max_length=100)
    signataire_titre = models.CharField("Titre (ex: Le Président)", max_length=100)
    signature = models.ImageField(
        "Signature (image)",
        upload_to="syndicats/signatures/",
        blank=True,
        null=True,
        help_text="Signature. Format PNG recommandé (superposée au cachet sur la carte).",
    )
    clause_legale = models.TextField(
        "Clause légale (VERSO)",
        blank=True,
        default="Les autorités civiles et militaires sont priées d'apporter toute leur assistance au porteur de la présente.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Syndicat"
        verbose_name_plural = "Syndicats"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class MemberCategory(models.Model):
    """Catégorie de membre (Propriétaire, Locataire, Membre du conseil, etc.)."""
    syndicat = models.ForeignKey(
        Syndicat,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name="Syndicat",
    )
    nom = models.CharField("Nom de la catégorie", max_length=100)
    ordre = models.PositiveSmallIntegerField("Ordre d'affichage", default=0)

    class Meta:
        verbose_name = "Catégorie de membre"
        verbose_name_plural = "Catégories de membres"
        ordering = ["syndicat", "ordre", "nom"]
        unique_together = [["syndicat", "nom"]]

    def __str__(self):
        return f"{self.nom} ({self.syndicat.nom})"


class Member(models.Model):
    """Membre d'un syndicat."""
    syndicat = models.ForeignKey(
        Syndicat,
        on_delete=models.CASCADE,
        related_name="membres",
        verbose_name="Syndicat",
    )
    categorie = models.ForeignKey(
        MemberCategory,
        on_delete=models.PROTECT,
        related_name="membres",
        verbose_name="Catégorie",
    )
    numero_membre = models.CharField("Numéro de membre", max_length=50, blank=True)
    prenom = models.CharField("Prénom", max_length=100)
    nom = models.CharField("Nom", max_length=100)
    email = models.EmailField(blank=True)
    telephone = models.CharField("Téléphone", max_length=20, blank=True)
    ministere_entreprise = models.CharField(
        "Ministère / Entreprise",
        max_length=200,
        blank=True,
        help_text="Ex: ENVIRONNEMENT, Finances...",
    )
    adresse = models.CharField("Adresse", max_length=255, blank=True)
    photo = models.ImageField(
        "Photo",
        upload_to="membres/photos/",
        blank=True,
        null=True,
    )
    date_adhesion = models.DateField("Date d'adhésion", null=True, blank=True)
    generated_card = models.ImageField(
        "Carte RECTO générée",
        upload_to="membres/cartes/",
        blank=True,
        null=True,
    )
    generated_card_back = models.ImageField(
        "Carte VERSO générée",
        upload_to="membres/cartes/",
        blank=True,
        null=True,
    )
    actif = models.BooleanField("Membre actif", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Membre"
        verbose_name_plural = "Membres"
        ordering = ["syndicat", "nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}".strip()

    def save(self, *args, **kwargs):
        if not self.numero_membre and self.syndicat_id and self.pk is None:
            count = Member.objects.filter(syndicat=self.syndicat).count()
            self.numero_membre = str(count + 1).zfill(5)
        super().save(*args, **kwargs)
