from django.urls import path
from . import views

app_name = "syndicat"

urlpatterns = [
    path("", views.home, name="home"),
    path("syndicats/", views.SyndicatListView.as_view(), name="syndicat_list"),
    path("syndicats/creer/", views.SyndicatCreateView.as_view(), name="syndicat_create"),
    path("syndicats/<int:pk>/", views.SyndicatDetailView.as_view(), name="syndicat_detail"),
    path("syndicats/<int:pk>/modifier/", views.SyndicatUpdateView.as_view(), name="syndicat_update"),
    path("syndicats/<int:pk>/categories/", views.categories_manage, name="categories_manage"),
    path("syndicats/<int:syndicat_pk>/membres/", views.MemberListView.as_view(), name="member_list"),
    path("syndicats/<int:syndicat_pk>/membres/ajouter/", views.MemberCreateView.as_view(), name="member_create"),
    path("membres/<int:pk>/", views.MemberDetailView.as_view(), name="member_detail"),
    path("membres/<int:pk>/modifier/", views.MemberUpdateView.as_view(), name="member_update"),
    path("membres/<int:pk>/carte/", views.member_card_display, name="member_card_display"),
    path("membres/<int:pk>/carte/pdf/", views.member_card_download_pdf, name="member_card_download_pdf"),
]
