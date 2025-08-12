from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView, UpdateView, DeleteView
from django.forms import inlineformset_factory
from datetime import datetime

from .models import (
    Table_Reservation,
    Profile,
    Menu,
    TableOrder,
    TableOrderItem,
    CartItem
)
from .forms import (
    CustomRegistrationForm,
    Table_ReservationForm,
    TableOrderForm,
    TableOrderItemForm
)
# ------------------ Formset Definition ------------------
TableOrderItemFormSet = inlineformset_factory(
    TableOrder,
    TableOrderItem,
    form=TableOrderItemForm,
    fields=('menu_item', 'quantity'),
    extra=1,
    can_delete=True
)

# ------------------ Home & Static Pages ------------------
def home_view(request):
    return render(request, 'home.html')

def reviews_view(request):
    return render(request, 'reviews.html')

# ------------------ Registration ------------------
class RegistrationView(FormView):
    template_name = 'registration.html'
    form_class = CustomRegistrationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        Profile.objects.create(
            user=user,
            phone_number=form.cleaned_data['phone_number'],
            address=form.cleaned_data['address']
        )
        login(self.request, user)
        return super().form_valid(form)

# ------------------ Login / Logout ------------------
class LoginView(DjangoLoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('view-reservation')

class LogoutView(DjangoLogoutView):
    next_page = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You’ve been successfully logged out.")
        return super().dispatch(request, *args, **kwargs)

# ------------------ Reservation: Create ------------------
class CreateReservationView(LoginRequiredMixin, View):
    template_name = 'create_reservation.html'
    success_url = reverse_lazy('view-reservation')

    def get(self, request):
        form = Table_ReservationForm()
        formset = TableOrderItemFormSet()
        return render(request, self.template_name, {'form': form, 'order_formset': formset})

    def post(self, request):
        form = Table_ReservationForm(request.POST)
        formset = TableOrderItemFormSet(request.POST)
        action = request.POST.get('action')

        if action == 'check_availability':
            if form.is_valid():
                table = form.cleaned_data['table']
                reservation_start = form.cleaned_data['reservation_start']
                reservation_end = form.cleaned_data['reservation_end']

                # Check if table is booked during this time
                is_booked = Table_Reservation.objects.filter(
                    table=table,
                    reservation_start__lt=reservation_end,
                    reservation_end__gt=reservation_start
                ).exists()

                if is_booked:
                    availability_message = f"Sorry, the table '{table.name}' is already booked during this time."
                else:
                    availability_message = f"Good news! The table '{table.name}' is available during this time."

                return render(request, self.template_name, {
                    'form': form,
                    'order_formset': formset,
                    'availability_message': availability_message
                })
            else:
                # Show form errors if invalid
                return render(request, self.template_name, {
                    'form': form,
                    'order_formset': formset
                })

        elif action == 'reserve':
            if form.is_valid() and formset.is_valid():
                reservation = form.save(commit=False)
                reservation.user = request.user
                reservation.save()

                table_order = TableOrder.objects.create(reservation=reservation)

                order_items = formset.save(commit=False)
                for item in order_items:
                    item.table_order = table_order
                    item.save()

                for obj in formset.deleted_objects:
                    obj.delete()

                messages.success(request, "Reservation created successfully!")
                return redirect(self.success_url)

            return render(request, self.template_name, {
                'form': form,
                'order_formset': formset
            })

        else:
            # Unknown action or no action
            return render(request, self.template_name, {
                'form': form,
                'order_formset': formset
            })

# ------------------ Reservation: View ------------------
class ViewReservationView(LoginRequiredMixin, ListView):
    model = Table_Reservation
    template_name = 'display_reservation.html'
    context_object_name = 'reservation'
    paginate_by = 10

    def get_queryset(self):
        table_name = self.request.GET.get('table_name')
        start_date = self.request.GET.get("start_date")

        filters = Q(user=self.request.user)

        if table_name:
            filters &= Q(table__name__icontains=table_name)
        if start_date:
            try:
                date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                filters &= Q(reservation_start__date=date_obj)
            except ValueError:
                pass

        return Table_Reservation.objects.filter(filters) \
            .prefetch_related('table_orders__items__menu_item') \
            .order_by('-reservation_start')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reservations = context['reservation']
        context['menu'] = Menu.objects.all()
        context['table'] = sorted(set(res.table.name for res in reservations))
        return context


# ------------------ Reservation: Update ------------------
class UpdateReservationView(LoginRequiredMixin, UpdateView):
    model = Table_Reservation
    form_class = Table_ReservationForm
    template_name = 'create_reservation.html'
    success_url = reverse_lazy('view-reservation')

    def get_table_order(self):
        """Ensure a TableOrder exists for this reservation"""
        table_order, created = TableOrder.objects.get_or_create(reservation=self.object)
        return table_order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table_order = self.get_table_order()

        if self.request.POST:
            context['order_formset'] = TableOrderItemFormSet(self.request.POST, instance=table_order)
        else:
            context['order_formset'] = TableOrderItemFormSet(instance=table_order)
        return context

    def form_valid(self, form):
        self.object = form.save()
        table_order = self.get_table_order()
        formset = TableOrderItemFormSet(self.request.POST, instance=table_order)

        if formset.is_valid():
            formset.save()
            messages.success(self.request, "Reservation updated successfully!")
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

# ------------------ Reservation: Delete ------------------
class DeleteReservationView(LoginRequiredMixin, DeleteView):
    model = Table_Reservation
    context_object_name = 'reservation'
    template_name = 'delete_reservation.html'
    success_url = reverse_lazy('view-reservation')

# ------------------ Table Orders ------------------
def add_to_table(request):
    if request.method == 'POST':
        form = TableOrderForm(request.POST)
        if form.is_valid():
            reservation_id = request.POST.get('reservation')
            reservation = get_object_or_404(Table_Reservation, pk=reservation_id)
            order = form.save(commit=False)
            order.reservation = reservation
            order.save()
            messages.success(request, f"Added order to table!")
            return redirect('view-reservation')
    else:
        form = TableOrderForm()

    return render(request, 'add_to_table.html', {
        'form': form,
        'reservations': Table_Reservation.objects.all(),
        'menu_items': Menu.objects.all()
    })

# ------------------ Menu Search + Detail ------------------
def search_menu(request):
    query = request.GET.get('query', '')
    results = Menu.objects.filter(item_name__icontains=query) if query else []
    return render(request, 'search_results.html', {'results': results, 'query': query})

class MenuDetailView(DetailView):
    model = Menu
    template_name = 'menu_detail.html'
    context_object_name = 'menu_item'

class MenuListView(ListView):
    model = Menu
    template_name = 'menu_list.html'         
    context_object_name = 'menu_items'


# ------------------ Cart ------------------
@login_required
def add_to_cart(request, pk):
    item = get_object_or_404(Menu, pk=pk)
    cart = request.session.get('cart', [])
    if pk not in cart:
        cart.append(pk)
        request.session['cart'] = cart
        messages.success(request, f"Added {item.item_name} to cart!")
    else:
        messages.info(request, f"{item.item_name} is already in your cart.")
    return redirect('menu_detail', pk=pk)

@login_required
def view_cart(request):
    cart = request.session.get('cart', [])
    menu_items = Menu.objects.filter(id__in=cart)
    reservations = Table_Reservation.objects.filter(user=request.user)

    return render(request, 'view_cart.html', {
        'menu_items': menu_items,
        'reservations': reservations
    })



@login_required
def add_cart_to_table(request, reservation_id):
    # Get reservation
    reservation = get_object_or_404(Table_Reservation, pk=reservation_id, user=request.user)

    # Get session cart
    cart = request.session.get('cart', [])
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    # Get or create TableOrder for the reservation
    table_order, created = TableOrder.objects.get_or_create(reservation=reservation)

    # Loop through cart items and add them to TableOrder
    for menu_id in cart:
        try:
            menu_item = Menu.objects.get(pk=menu_id)
        except Menu.DoesNotExist:
            continue  # Skip if item doesn't exist

        # Check if item already exists in the order
        item, created = TableOrderItem.objects.get_or_create(
            order=table_order,  # ✅ Ensure this matches your FK name!
            menu_item=menu_item,
            defaults={'quantity': 1}
        )
        if not created:
            item.quantity += 1
            item.save()

    # Clear cart
    request.session['cart'] = []
    messages.success(request, "Cart items added to reservation!")
    return redirect('view-reservation')

@login_required
def check_availability(request):
    date = request.GET.get('date')
    time = request.GET.get('time')

    if not date or not time:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        check_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return JsonResponse({'error': 'Invalid date or time format'}, status=400)

    check_end = check_start + timezone.timedelta(hours=2)  # assuming a 2-hour reservation

    booked_table_ids = Table_Reservation.objects.filter(
        reservation_start__lt=check_end,
        reservation_end__gt=check_start
    ).values_list('table_id', flat=True)

    Table = Table_Reservation._meta.get_field('table').related_model
    all_tables = Table.objects.all()

    tables = []
    for table in all_tables:
        tables.append({
            'id': table.id,
            'name': table.name,
            'status': 'Booked' if table.id in booked_table_ids else 'Available'
        })

    return JsonResponse({'tables': tables})
