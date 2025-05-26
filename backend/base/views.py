from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views import View
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django.contrib.auth import login
#from .forms import SignUpForm
from .models import Produit

from .products import products 
from .models import Produit, Cart, CartItem, Commande, Client
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from collections import defaultdict
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import CustomUserSignupForm

class Home(View):
    def get(self, request):
        produits = Produit.objects.all()
        return render(request, 'accueil.html', {'produits': produits})

    
class Produitlist(View):
        def get(self, request):
            produits = Produit.objects.all()  
            return render(request, 'produit.html', {'produit': produits})
        
    

class ProduitDetail(View):
    def get(self, request, id):
        produit = get_object_or_404(Produit, id=id)
        return render(request, 'produit_detail.html', {'produit': produit})
    


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.is_staff:
                return redirect('/admin/')
            else:
                return redirect('home')  # ou 'products'
    else:
        form = CustomUserSignupForm()
    return render(request, 'register.html', {'form': form})

    
def cart_view(request):
    return render(request, 'cart.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('/admin/')
            else:
                return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Identifiants invalides'})
    return render(request, 'login.html')


@require_POST
@login_required(login_url='login')
def add_to_cart(request, id):
    produit = get_object_or_404(Produit, id=id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    cart_item, created = CartItem.objects.get_or_create(cart=cart, produit=produit)
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    messages.success(request, f"{produit.name} ajouté au panier.")
    return redirect('produit_detail', id=id)
@login_required(login_url='login')
def cart_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    items = CartItem.objects.filter(cart=cart) if cart else []

    categories = defaultdict(list)
    total_general = 0

    for item in items:
        cat = item.produit.category or "Sans catégorie"
        subtotal = item.quantity * float(item.produit.price)
        categories[cat].append({
            'produit': item.produit,
            'quantity': item.quantity,
            'subtotal': subtotal,
            'item_id': item.id 
        })
        total_general += subtotal

    return render(request, 'cart.html', {
        'categories': dict(categories),
        'total_general': total_general
    })

@login_required(login_url='login')
def checkout_view(request):
    product_id = request.GET.get('product_id')
    produits = []
    total = 0

    if product_id:
        produit = get_object_or_404(Produit, id=product_id)
        produits = [produit]
        total = float(produit.price)
    else:
        cart = Cart.objects.filter(user=request.user).first()
        items = CartItem.objects.filter(cart=cart) if cart else []
        produits = [item.produit for item in items]
        total = sum(item.quantity * float(item.produit.price) for item in items)

    if request.method == 'POST':
        Commande.objects.create(
            user=request.user,
            shippingAddress=request.POST['address'],
            city=request.POST['city'],
            postalCode=request.POST['postal'],
            country=request.POST['country'],
            totalPrice=total
        )
        if not product_id:
            CartItem.objects.filter(cart=cart).delete()
        request.session['cart'] = {}
        return redirect('profile')

    return render(request, 'checkout.html', {'total': total})


def profile_view(request):
    commandes = Commande.objects.filter(user=request.user)

    try:
        profil_client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        profil_client = None

    return render(request, 'profile.html', {
        'commandes': commandes,
        'profil_client': profil_client,
        'user': request.user
    })




def custom_logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')
        


class ProduitParCategorie(View):
    def get(self, request, categorie):
        produits = Produit.objects.filter(category__iexact=categorie)
        return render(request, 'produit_categorie.html', {
            'categorie': categorie,
            'produits': produits
        })




@login_required(login_url='login')
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    return redirect('cart')


from django.db.models import Q

def search_produits(request):
    query = request.GET.get('q', '')
    produits = Produit.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    ) if query else []

    return render(request, 'search_results.html', {
        'query': query,
        'produits': produits
    })





def register_view(request):
    if request.method == 'POST':
        form = CustomUserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserSignupForm()
    return render(request, 'register.html', {'form': form})
@require_POST
@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    try:
        new_quantity = int(request.POST.get('quantity'))
        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, f"Quantité de {cart_item.produit.name} mise à jour.")
    except (ValueError, TypeError):
        messages.error(request, "Quantité invalide.")
    return redirect('cart')



# Create your views here.
