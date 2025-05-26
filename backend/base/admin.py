from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import path
from django.utils.html import format_html
from django.template.response import TemplateResponse

from .models import Produit, Review, Commande, Client

# ✅ Admin personnalisé avec dashboard
class CustomAdminSite(admin.AdminSite):
    site_header = "Admin Dashboard"
    site_title = "SITE Admin"
    index_title = "Bienvenue sur le tableau de bord"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_view(self.dashboard_view), name='admin-dashboard'),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        total_produits = Produit.objects.count()
        total_commandes = Commande.objects.count()
        total_utilisateurs = User.objects.count()

        context = dict(
            self.each_context(request),
            total_produits=total_produits,
            total_commandes=total_commandes,
            total_utilisateurs=total_utilisateurs
        )
        return TemplateResponse(request, "admin/dashboard.html", context)

# ✅ Activer le site personnalisé
admin_site = CustomAdminSite()
admin.site = admin_site

# ✅ Enregistrement des autres modèles
admin.site.register(Produit)



# ✅ Admin des commandes stylé avec statut modifiable
class CommandeAdmin(admin.ModelAdmin):
    list_display = [
        'user_display', 'total_display', 'adresse_display', 'ville_display',
        'statut_badge', 'isPaid', 'isDelivered', 'createdAt'
    ]
    list_filter = ['is_validated', 'isPaid', 'isDelivered', 'createdAt']
    list_editable = ['isPaid', 'isDelivered']  # ✅ modifiables en ligne
    search_fields = ['user__username', 'city', 'shippingAddress']
    ordering = ['-createdAt']
    actions = ['valider_commandes']

    @admin.action(description="✅ Valider les commandes sélectionnées")
    def valider_commandes(self, request, queryset):
        updated = queryset.update(is_validated=True)
        self.message_user(request, f"{updated} commande(s) validée(s) avec succès.")

    def statut_badge(self, obj):
        if obj.is_validated:
            return format_html('<span class="badge bg-success">✔ Validée</span>')
        return format_html('<span class="badge bg-danger">✖ En attente</span>')
    statut_badge.short_description = "Statut"

    def user_display(self, obj):
        return format_html(f'<span class="text-primary fw-bold">{obj.user.username}</span>')
    user_display.short_description = "Client"

    def total_display(self, obj):
        return format_html(f'<span class="badge bg-dark">{obj.totalPrice:.2f} DH</span>')
    total_display.short_description = "Total"

    def adresse_display(self, obj):
        return format_html(f'<span class="text-muted small">{obj.shippingAddress}</span>')
    adresse_display.short_description = "Adresse"

    def ville_display(self, obj):
        return format_html(f'<span class="text-info">{obj.city}</span>')
    ville_display.short_description = "Ville"

# ✅ Enregistrement dans le CustomAdminSite
admin.site.register(Commande, CommandeAdmin)
# ✅ Enregistrement du modèle Client
admin.site.register(Client)
