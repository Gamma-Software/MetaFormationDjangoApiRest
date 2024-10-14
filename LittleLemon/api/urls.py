"""
URL configuration for LittleLemon project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    # Admin and Manager endpoints
    path("groups/users/", views.ManageGroupView.as_view(), name="manage-groups"),
    path("menu-items/", views.add_menu_item, name="add-menu-item"),
    path("categories/", views.add_category, name="add-category"),
    path(
        "menu-items/featured/",
        views.update_item_of_the_day,
        name="update-featured-item",
    ),
    path(
        "groups/delivery-crew/users/",
        views.assign_delivery_crew,
        name="assign-delivery-crew",
    ),
    path("orders/assign/", views.assign_orders_to_delivery_crew, name="assign-orders"),
    # Delivery Crew endpoints
    path("orders/crew/", views.get_assigned_orders, name="crew-orders"),
    path("orders/status/", views.update_order_status, name="update-order-status"),
    # Customer endpoints
    path("categories/", views.get_categories, name="categories"),
    path("menu-items/", views.get_menu_items, name="menu-items"),
    path("menu-items/<int:pk>/", views.MenuItemView.as_view(), name="menu-item-detail"),
    path("orders/", views.OrderView.as_view(), name="orders"),
    path("cart/", views.get_cart, name="get_cart"),
    path("cart/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
]
