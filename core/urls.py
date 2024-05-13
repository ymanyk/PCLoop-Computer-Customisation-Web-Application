from django.urls import path, include
from core.views import add_to_cart, add_to_wishlist, ajax_contact_form, cart_view, category_list_view, category_product_list_view, checkout_view, contact, customer_dashboard, delete_item_from_cart, filter_product, index, make_address_default, order_detail, payment_completed_view, payment_failed_view, product_detail_view, product_list_view, remove_wishlist, search_view, tag_list, ajax_add_review, update_cart, vendor_detail_view, vendor_list_view, wishlist_view
from core.views import customize_pc, confirm_view, checkout2_view
from . import views
app_name = "core"

urlpatterns = [
    path("", index, name="index"),
    path("products/", product_list_view, name="product-list"),
    path("product/<pid>", product_detail_view, name="product-detail"),
    path("vendors/", vendor_list_view, name="vendor-list"),
    path("vendor/<vid>", vendor_detail_view, name="vendor-detail"),
    path("category/", category_list_view, name="category-list"),
    path("category/<cid>", category_product_list_view, name="category-product-list"),
    path("products/tag/<slug:tag_slug>/", tag_list, name="tags"),
    path("ajax-add-review/<int:pid>/", ajax_add_review, name="ajax-add-review"),
    path("search/", search_view, name="search"),
    path("filter-products/", filter_product, name="filter-product"),
    path("add-to-cart/", add_to_cart, name="add-to-cart"),
    path("cart/", cart_view, name="cart"),
    path("delete-from-cart/", delete_item_from_cart, name="delete-from-cart"),
    path("update-cart/", update_cart, name="update-cart"),
    path("checkout/", checkout_view, name="checkout"),
    path('paypal/', include('paypal.standard.ipn.urls')),
    path("payment-completed/", payment_completed_view, name="payment-completed"),
    path("payment-failed/", payment_failed_view, name="payment-failed"),
    path("dashboard/", customer_dashboard, name="dashboard"),
    path("dashboard/order/<int:id>", order_detail, name="order-detail"),
    path("make-default-address/", make_address_default, name="make-default-address"),
    path("wishlist/", wishlist_view, name="wishlist"),
    path("add-to-wishlist/", add_to_wishlist, name="add-to-wishlist"),
    path("remove-from-wishlist/", remove_wishlist, name="remove-from-wishlist"),
    path("contact/", contact, name="contact"),
    path("ajax-contact-form/", ajax_contact_form, name="ajax-contact-form"),

    # customise
    path("customize/", customize_pc, name="customize_pc"),
    path("confirm/", checkout2_view, name="confirm"),
    path("api/products/<int:category_id>/", views.get_products, name="get_products"),
    path("api/product/<str:product_id>/", views.product_detail, name="product_detail"),
    path("checkout2/", checkout2_view, name="checkout2"),

]