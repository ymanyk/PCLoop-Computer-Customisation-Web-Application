from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from userauths.models import ContactUs, Profile
from core.models import Product, Category, Vendor, CartOrder, CartOrderItems, ProductImages, ProductReview, Wishlist, Address
from django.db.models import Count, Avg
from taggit.models import Tag
from core.forms import ProductReviewForm
from django.template.loader import render_to_string
from django.contrib import messages

from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from django.contrib.auth.decorators import login_required

from django.core import serializers
import calendar
from django.db.models import Count, Avg
from django.db.models.functions import ExtractMonth

# Create your views here.
def index(request):
    products = Product.objects.filter(product_status="published", featured=True)
    context = {
        "products":products
    }
    return render(request, 'core/index.html', context)

def product_list_view(request):
    products = Product.objects.filter(product_status="published")
    context = {
        "products":products
    }
    return render(request, 'core/product-list.html', context)

def product_detail_view(request, pid):
    product = Product.objects.get(pid=pid)
    products = Product.objects.filter(category=product.category).exclude(pid=pid)
    reviews = ProductReview.objects.filter(product=product).order_by("-date")
    average_rating = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))
    review_form = ProductReviewForm()
    
    make_review = True
    if request.user.is_authenticated:
        user_review_count = ProductReview.objects.filter(user=request.user, product=product).count()

        if user_review_count > 0:
            make_review = False

    p_image = product.p_images.all()
    context = {
        "p": product,
        "p_image": p_image,
        "products": products,
        "reviews": reviews,
        "average_rating": average_rating,
        "review_form": review_form,
        "make_review": make_review,
    }
    return render(request, 'core/product-detail.html', context)

def vendor_list_view(request):
    vendors = Vendor.objects.all()
    context = {
        "vendors":vendors
    }
    return render(request, 'core/vendor-list.html', context)

def vendor_detail_view(request, vid):
    vendor = Vendor.objects.get(vid=vid)
    products = Product.objects.filter(vendor=vendor,product_status="published")
    context = {
        "vendor":vendor,
        "products":products,
    }
    return render(request, 'core/vendor-detail.html', context)

def category_list_view(request):
    categories = Category.objects.all().annotate(product_count=Count('category'))
    context = {
        "categories":categories
    }
    return render(request, 'core/category-list.html', context)

def category_product_list_view(request, cid):
    category = Category.objects.get(cid=cid)
    products = Product.objects.filter(product_status="published", category=category)

    context = {
        "category":category,
        "products":products,
    }
    return render(request, 'core/category-product-list.html', context)

def tag_list(request, tag_slug=None):
    products = Product.objects.filter(product_status="published").order_by("-id")

    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        products = products.filter(tags__in=[tag])

    context = {
        "products":products,
        "tag":tag,
    }
    return render(request, 'core/tag.html', context)

def ajax_add_review(request, pid):
    product = Product.objects.get(pk=pid)
    user = request.user
    
    review = ProductReview.objects.create(
        user=user,
        product=product,
        review = request.POST['review'],
        rating = request.POST['rating'],
    )

    context = {
        'user': user.username,
        'review': request.POST['review'],
        'rating': request.POST['rating'],
    }
    average_reviews = ProductReview.objects.filter(product=product).aggregate(rating=Avg("rating"))
    return JsonResponse(
        {
        'bool': True,
        'context': context,
        'average_reviews': average_reviews
        }
    )

def search_view(request):
    query = request.GET.get("q")

    products = Product.objects.filter(title__icontains=query).order_by("-date").distinct()

    context = {
        "products": products,
        "query": query,
    }
    return render(request, "core/search.html", context)

def filter_product(request):
    categories = request.GET.getlist("category[]")
    vendors = request.GET.getlist("vendor[]")

    min_price = request.GET['min_price']
    max_price = request.GET['max_price']

    products = Product.objects.filter(product_status="published").order_by("-id").distinct()

    products = products.filter(price__gte=min_price) #gte means >=
    products = products.filter(price__lte=max_price)

    if len(categories) > 0:
        products = products.filter(category__id__in=categories).distinct() 
    # else:
    #     products = Product.objects.filter(product_status="published").order_by("-id").distinct()
    if len(vendors) > 0:
        products = products.filter(vendor__id__in=vendors).distinct() 
    # else:
    #     products = Product.objects.filter(product_status="published").order_by("-id").distinct()    
    
    data = render_to_string("core/async/product-list.html", {"products": products})
    return JsonResponse({"data": data})

def add_to_cart(request):
    cart_product = {}

    cart_product[str(request.GET['id'])] = {
        'title': request.GET['title'],
        'qty': request.GET['qty'],
        'price': request.GET['price'],
        'image': request.GET['image'],
        'pid': request.GET['pid'],
    }

    if 'cart_data_obj' in request.session:
        if str(request.GET['id']) in request.session['cart_data_obj']:

            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = int(cart_product[str(request.GET['id'])]['qty'])
            cart_data.update(cart_data)
            request.session['cart_data_obj'] = cart_data
        else:
            cart_data = request.session['cart_data_obj']
            cart_data.update(cart_product)
            request.session['cart_data_obj'] = cart_data

    else:
        request.session['cart_data_obj'] = cart_product
    return JsonResponse({"data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj'])})

def cart_view(request):
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])
        return render(request, "core/cart.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
    else:
        messages.warning(request, "Your cart is empty")
        return redirect("core:index")
    
def delete_item_from_cart(request):
    product_id = str(request.GET['id'])
    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            del request.session['cart_data_obj'][product_id]
            request.session['cart_data_obj'] = cart_data
    
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj'])})

def update_cart(request):
    product_id = str(request.GET['id'])
    product_qty = request.GET['qty']

    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = product_qty
            request.session['cart_data_obj'] = cart_data
    
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj'])})

@login_required
def checkout_view(request):
    cart_total_amount = 0
    total_amount = 0

    # Checking if cart_data_obj session exists
    if 'cart_data_obj' in request.session:

        # Getting total amount for Paypal Amount
        for p_id, item in request.session['cart_data_obj'].items():
            total_amount += int(item['qty']) * float(item['price'])

        # Create ORder Object
        order = CartOrder.objects.create(
            user=request.user,
            price=total_amount
        )

        # Getting total amount for The Cart
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

            cart_order_products = CartOrderItems.objects.create(
                order=order,
                invoice_no="INVOICE_NO-" + str(order.id), # INVOICE_NO-5,
                item=item['title'],
                image=item['image'],
                qty=item['qty'],
                price=item['price'],
                total=float(item['qty']) * float(item['price'])
            )

        host = request.get_host()
        paypal_dict = {
            'business': settings.PAYPAL_RECEIVER_EMAIL,
            'amount': cart_total_amount,
            'item_name': "Order-Item-No-" + str(order.id),
            'invoice': "INVOICE_NO-" + str(order.id),
            'currency_code': "MYR",
            'notify_url': 'http://{}{}'.format(host, reverse("core:paypal-ipn")),
            'return_url': 'http://{}{}'.format(host, reverse("core:payment-completed")),
            'cancel_url': 'http://{}{}'.format(host, reverse("core:payment-failed")),
        }

        paypal_payment_button = PayPalPaymentsForm(initial=paypal_dict)

        try:
            active_address = Address.objects.get(user=request.user, status=True)
        except:
            messages.warning(request, "")
            active_address = None

        return render(request, "core/checkout.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount, 'paypal_payment_button':paypal_payment_button, 'active_address':active_address})

@login_required
def checkout2_view(request):
    if request.method == "POST":
        # Extracting and loading the JSON string of selected product IDs
        selected_product_ids = json.loads(request.POST.get("products", "[]"))
        subtotal = 0.00
        request.session["cart_data_obj"] = {}
        # Assuming there's a mechanism to get the price of each product by its ID
        for product_id in selected_product_ids:
            try:
                product = Product.objects.get(pid=product_id)
                add_item_to_cart(
                    request,
                    product_id=str(product.pid),
                    title=str(product.title),
                    qty=1,
                    price=str(product.price),
                    image=product.image,
                    pid=str(product.pid),
                )
                subtotal += float(product.price)
            except Product.DoesNotExist:
                # Handle case where product is not found
                continue

        if subtotal <= 0:
            messages.error(
                request, "Subtotal is invalid. Please go back and customize your PC."
            )
            return redirect("core:customize_pc")

    # Create a new order object
    order = CartOrder.objects.create(user=request.user, price=subtotal)

    # Create order items for each selected product
    for product_id in selected_product_ids:
        try:
            product = Product.objects.get(pid=product_id)
            CartOrderItems.objects.create(
                order=order, item=product.title, price=product.price
            )
        except Product.DoesNotExist:
            # Handle case where product is not found
            pass

    # PayPal payment dictionary
    host = request.get_host()
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": subtotal,
        "item_name": "Order-Item-No-" + str(order.id),
        "invoice": "INVOICE_NO-" + str(order.id),
        "currency_code": "MYR",
        "notify_url": "http://{}{}".format(host, reverse("core:paypal-ipn")),
        "return_url": "http://{}{}".format(host, reverse("core:payment-completed")),
        "cancel_url": "http://{}{}".format(host, reverse("core:payment-failed")),
    }

    paypal_payment_button2 = PayPalPaymentsForm(initial=paypal_dict)
    return render(
        request,
        "core/confirm.html",
        {"subtotal": subtotal, "paypal_payment_button2": paypal_payment_button2},
    )

def add_item_to_cart(request, product_id, title, qty, price, image, pid):
    image_url = request.build_absolute_uri(image.url) if image else ""
    cart_product = {
        str(product_id): {
            "title": title,
            "qty": qty,
            "price": price,
            "image": image_url,
            "pid": pid,
        }
    }

    if "cart_data_obj" in request.session:
        cart_data = request.session["cart_data_obj"]
        if str(product_id) in cart_data:
            # Update quantity if product already in cart
            cart_data[str(product_id)]["qty"] += int(qty)
        else:
            # Add new product to cart
            cart_data.update(cart_product)
    else:
        # Create new cart with this product
        cart_data = cart_product

    request.session["cart_data_obj"] = cart_data


@login_required
def payment_completed_view(request):
    cart_total_amount = 0
    if "cart_data_obj" in request.session:
        for p_id, item in request.session["cart_data_obj"].items():
            cart_total_amount += int(item["qty"]) * float(item["price"])
    return render(
        request,
        "core/payment-completed.html",
        {
            "cart_data": request.session["cart_data_obj"],
            "totalcartitems": len(request.session["cart_data_obj"]),
            "cart_total_amount": cart_total_amount,
        },
    )

@login_required
def payment_failed_view(request):
    return render(request, 'core/payment-failed.html')

@login_required
def customer_dashboard(request):
    orders_list= CartOrder.objects.filter(user=request.user).order_by("-id")
    address = Address.objects.filter(user=request.user)
    contact_messages = ContactUs.objects.all()

    orders = CartOrder.objects.annotate(month=ExtractMonth("order_date")).values("month").annotate(count=Count("id")).values("month", "count")
    month = []
    total_orders = []

    for i in orders:
        month.append(calendar.month_name[i["month"]])
        total_orders.append(i["count"])

    if request.method == "POST":
        address = request.POST.get("address")
        mobile = request.POST.get("mobile")

        new_address = Address.objects.create(
            user=request.user,
            address=address,
            mobile=mobile,
            orders=orders,
        )
        messages.success(request, "Address Added Successfully.")
        return redirect("core:dashboard")
    else:
        print("Error")

    user_profile = Profile.objects.get(user=request.user)
    print("user profile is: #########################",  user_profile)

    context = {
        "user_profile": user_profile,
        "orders_list": orders_list,
        "orders": orders,
        "address": address,
        "month": month,
        "total_orders": total_orders,
        "contact_messages":contact_messages,
        
    }
    return render(request, 'core/dashboard.html', context)

def order_detail(request, id):
    order = CartOrder.objects.get(user=request.user, id=id)
    order_items = CartOrderItems.objects.filter(order=order)

    
    context = {
        "order_items": order_items,
    }
    return render(request, 'core/order-detail.html', context)

def make_address_default(request):
    id = request.GET['id']
    Address.objects.update(status=False)
    Address.objects.filter(id=id).update(status=True)
    return JsonResponse({"boolean": True})

@login_required
def wishlist_view(request):
    wishlist = Wishlist.objects.all()
    context = {
        "w":wishlist
    }
    return render(request, "core/wishlist.html", context)

def add_to_wishlist(request):
    product_id = request.GET['id']
    product = Product.objects.get(id=product_id)
    print("product id is:" + product_id)

    context = {}

    wishlist_count = Wishlist.objects.filter(product=product, user=request.user).count()
    print(wishlist_count)

    if wishlist_count > 0:
        context = {
            "bool": True
        }
    else:
        new_wishlist = Wishlist.objects.create(
            user=request.user,
            product=product,
        )
        context = {
            "bool": True
        }

    return JsonResponse(context)

def remove_wishlist(request):
    pid = request.GET['id']
    wishlist = Wishlist.objects.filter(user=request.user)
    wishlist_d = Wishlist.objects.get(id=pid)
    delete_product = wishlist_d.delete()
    
    context = {
        "bool":True,
        "w":wishlist
    }
    wishlist_json = serializers.serialize('json', wishlist)
    t = render_to_string('core/async/wishlist-list.html', context)
    return JsonResponse({'data':t,'w':wishlist_json})

def contact(request):
    return render(request, "core/contact.html")


def ajax_contact_form(request):
    full_name = request.GET['full_name']
    email = request.GET['email']
    phone = request.GET['phone']
    subject = request.GET['subject']
    message = request.GET['message']

    contact = ContactUs.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        subject=subject,
        message=message,
    )

    data = {
        "bool": True,
        "message": "Message Sent Successfully"
    }

    return JsonResponse({"data":data})


def about_us(request):
    return render(request, "core/about_us.html")

def purchase_guide(request):
    return render(request, "core/purchase_guide.html")

def privacy_policy(request):
    return render(request, "core/privacy_policy.html")

def terms_of_service(request):
    return render(request, "core/terms_of_service.html")


# customize

from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Category, Product


def customize_pc(request):
    categories = Category.objects.all()
    products = Product.objects.all()  # Fetch all products initially
    return render(request, "core/customize_pc.html", {"categories": categories})


def get_products(request, category_id):
    products = Product.objects.filter(category_id=category_id)
    options = []
    for product in products:
        option = {"value": product.pid, "text": product.title, "price": product.price}
        options.append(option)
    return JsonResponse({"options": options})


def confirm_view(request):
    if request.method == "POST":
        selected_product_ids = request.POST.getlist("products")
        selected_products = []
        subtotal = 0.00  # Initialize subtotal
        for product_id in selected_product_ids:
            try:
                product = Product.objects.get(id=int(product_id))
                selected_products.append(product)
                subtotal += product.price  # Add product price to subtotal
            except (Product.DoesNotExist, ValueError):
                # Handle cases where the product does not exist or the ID is not valid
                pass
        # Store subtotal in session (if needed)
        request.session["subtotal"] = subtotal

        # You might want to store total_budget in session as well if it's used elsewhere

        return render(
            request,
            "core/confirm.html",
            {"selected_products": selected_products, "subtotal": subtotal},
        )
    else:
        # If it's not a POST request, redirect to customize_pc page
        return redirect("core:customize_pc")


import json


def product_detail(request, product_id):
    try:
        product = json.loads(
            serializers.serialize("json", [Product.objects.get(pid=product_id)])
        )[0]["fields"]
        # Assuming 'Product' model has 'image_url', 'title', 'price' fields
        data = {
            "image_url": f"http://{request.get_host()}/media/user_1/{product['image'].split('/')[-1]}",
            "title": product["title"],
            "price": product["price"],
            "url": request.get_host(),
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)
    
