from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .forms import MemberCategoryForm, MemberForm, SyndicatForm
from .models import Member, MemberCategory, Syndicat


def home(request):
    return redirect("syndicat:syndicat_list")


class SyndicatListView(ListView):
    model = Syndicat
    context_object_name = "syndicats"
    template_name = "syndicat/syndicat_list.html"


class SyndicatDetailView(DetailView):
    model = Syndicat
    context_object_name = "syndicat"
    template_name = "syndicat/syndicat_detail.html"


class SyndicatCreateView(CreateView):
    model = Syndicat
    form_class = SyndicatForm
    template_name = "syndicat/syndicat_form.html"

    def get_success_url(self):
        return reverse("syndicat:syndicat_detail", kwargs={"pk": self.object.pk})


class SyndicatUpdateView(UpdateView):
    model = Syndicat
    form_class = SyndicatForm
    context_object_name = "syndicat"
    template_name = "syndicat/syndicat_form.html"

    def get_success_url(self):
        return reverse("syndicat:syndicat_detail", kwargs={"pk": self.object.pk})


def categories_manage(request, pk):
    syndicat = get_object_or_404(Syndicat, pk=pk)
    categories = syndicat.categories.all()
    if request.method == "POST":
        form = MemberCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.syndicat = syndicat
            cat.save()
            messages.success(request, "Catégorie ajoutée.")
            return redirect("syndicat:categories_manage", pk=pk)
    else:
        form = MemberCategoryForm()
    return render(
        request,
        "syndicat/categories_manage.html",
        {"syndicat": syndicat, "categories": categories, "form": form},
    )


class MemberListView(ListView):
    template_name = "syndicat/member_list.html"
    context_object_name = "membres"

    def get_queryset(self):
        self.syndicat = get_object_or_404(Syndicat, pk=self.kwargs["syndicat_pk"])
        return self.syndicat.membres.select_related("categorie").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["syndicat"] = self.syndicat
        return context


class MemberDetailView(DetailView):
    model = Member
    context_object_name = "member"
    template_name = "syndicat/member_detail.html"


class MemberCreateView(CreateView):
    model = Member
    form_class = MemberForm
    template_name = "syndicat/member_form.html"

    def get_initial(self):
        initial = super().get_initial()
        syndicat = get_object_or_404(Syndicat, pk=self.kwargs["syndicat_pk"])
        initial["syndicat"] = syndicat
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["syndicat"] = get_object_or_404(Syndicat, pk=self.kwargs["syndicat_pk"])
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["syndicat"] = get_object_or_404(Syndicat, pk=self.kwargs["syndicat_pk"])
        return kwargs

    def get_success_url(self):
        return reverse("syndicat:member_list", kwargs={"syndicat_pk": self.object.syndicat_id})


class MemberUpdateView(UpdateView):
    model = Member
    form_class = MemberForm
    context_object_name = "member"
    template_name = "syndicat/member_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["syndicat"] = self.get_object().syndicat
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["syndicat"] = self.get_object().syndicat
        return kwargs

    def get_success_url(self):
        return reverse("syndicat:member_list", kwargs={"syndicat_pk": self.object.syndicat_id})


def member_card_display(request, pk):
    """Génère et affiche la carte de membre (RECTO + VERSO PNG)."""
    member = get_object_or_404(Member, pk=pk)
    try:
        from .card_generator import generate_card_image
        generate_card_image(member.pk)
        member.refresh_from_db()
    except Exception as e:
        return render(
            request,
            "syndicat/member_card_error.html",
            {"member": member, "error": str(e)},
            status=500,
        )
    return render(
        request,
        "syndicat/member_card_display.html",
        {"member": member, "syndicat": member.syndicat},
    )


def member_card_download_pdf(request, pk):
    """Télécharge la carte de membre en PDF (format PVC 86×54 mm)."""
    member = get_object_or_404(Member, pk=pk)
    try:
        from .card_generator import generate_card_image
        generate_card_image(member.pk)
        member.refresh_from_db()
    except Exception:
        messages.error(request, "Impossible de générer la carte.")
        return redirect("syndicat:member_detail", pk=pk)

    if not member.generated_card or not member.generated_card_back:
        messages.error(request, "La carte n'a pas pu être générée.")
        return redirect("syndicat:member_detail", pk=pk)

    from io import BytesIO

    buffer = BytesIO()
    page_w = 86 * mm
    page_h = 54 * mm
    c = canvas.Canvas(buffer, pagesize=(page_w, page_h))

    for img_field in [member.generated_card, member.generated_card_back]:
        path = img_field.path
        c.drawImage(path, 0, 0, width=page_w, height=page_h)
        c.showPage()

    c.save()
    buffer.seek(0)
    filename = f"carte_{member.nom}_{member.prenom}.pdf".replace(" ", "_")

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

