from django.contrib.auth.models import User, Group
from rest_framework import generics, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import MenuItem, Category, Order, Cart
from .serializers import (
    UserSerializer,
    MenuItemSerializer,
    CategorySerializer,
    OrderSerializer,
    CartSerializer,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import BasePermission
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class IsGroupUser(BasePermission):
    group = None

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.groups.filter(name=self.group).exists()


class IsManager(IsGroupUser):
    group = "managers"


class IsCrew(IsGroupUser):
    group = "crew"


# The admin can assign users to the manager group
class ManageGroupView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def update(self, request, *args, **kwargs):
        user = get_object_or_404(User, id=kwargs["pk"])
        group_to_assign = request.data["group"]
        if group_to_assign == "managers":
            manager_group = Group.objects.get(name=group_to_assign)
            if manager_group not in user.groups.all():
                user.groups.add(manager_group)
            else:
                return Response(
                    {"message": "User already in manager group"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif group_to_assign == "delivery crew":
            delivery_crew_group = Group.objects.get(name=group_to_assign)
            if delivery_crew_group not in user.groups.all():
                user.groups.add(delivery_crew_group)
            else:
                return Response(
                    {"message": "User already in delivery crew group"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response({"message": "User assigned to manager group successfully"})

    def delete(self, request, *args, **kwargs):
        user = get_object_or_404(User, id=kwargs["pk"])
        group_to_assign = request.data["group"]
        group = Group.objects.get(name=group_to_assign)
        if group in user.groups.all():
            user.groups.remove(group)
        return Response({"message": "User removed from manager group successfully"})

    def get(self, request, *args, **kwargs):
        user = get_object_or_404(User, id=kwargs["pk"])
        if "managers" in user.groups.all():
            return Response({"message": "User is a manager"})
        elif "delivery crew" in user.groups.all():
            return Response({"message": "User is a delivery crew"})
        return Response({"message": "User is not a manager or delivery crew"})


# The admin can add menu items
@api_view(["POST"])
@permission_classes([permissions.IsAdminUser])
def add_menu_item(request):
    if request.method == "POST":
        serializer = MenuItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(
        {"message": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


# The admin can add categories
@api_view(["POST"])
@permission_classes([permissions.IsAdminUser])
def add_category(request):
    if request.method == "POST":
        category = Category.objects.create(
            title=request.data["title"],
            slug=request.data["slug"],
        )
        return Response(
            {"message": f"Category {category.title} added successfully"},
            status=status.HTTP_201_CREATED,
        )
    return Response(
        {"message": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


# Managers can update the item of the day
@api_view(["PUT"])
@permission_classes([permissions.IsAdminUser, IsManager])
def update_item_of_the_day(request):
    if request.method == "PUT":
        menu_item = MenuItem.objects.get(id=request.data["id"])
        menu_item.featured = request.data["featured"]
        menu_item.save()
        return Response(
            {"message": f"Item {menu_item.title} of the day updated successfully"},
            status=status.HTTP_200_OK,
        )
    return Response(
        {"message": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


# Managers can assign users to the delivery crew
@api_view(["PUT"])
@permission_classes([permissions.IsAdminUser, IsManager])
def assign_delivery_crew(request):
    if request.method == "PUT":
        user = User.objects.get(id=request.data["id"])
        delivery_crew_group = Group.objects.get(name="Delivery Crew")
        user.groups.add(delivery_crew_group)
        return Response(
            {"message": f"User {user.username} assigned to delivery crew successfully"},
            status=status.HTTP_200_OK,
        )
    return Response(
        {"message": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


@api_view(["POST"])
@permission_classes([permissions.IsAdminUser, IsManager])
def assign_orders_to_delivery_crew(request):
    if request.method == "POST":
        order = Order.objects.get(id=request.data["order"])
        crew = User.objects.get(id=request.data["crew"])
        order.delivery_crew = crew
        return Response(
            {"message": f"Order assigned to delivery crew successfully"},
            status=status.HTTP_200_OK,
        )
    return Response(
        {"message": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


# The delivery crew can access orders assigned to them
@api_view(["GET"])
@permission_classes([permissions.IsAdminUser, IsCrew])
def get_assigned_orders(request):
    if request.method == "GET":
        orders = Order.objects.filter(delivery_crew=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(
        {"message": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


# The delivery crew can update an order as delivered
@api_view(["PUT"])
@permission_classes([permissions.IsAdminUser, IsCrew])
def update_order_status(request):
    if request.method == "PUT":
        order = Order.objects.get(id=request.data["id"])
        order.status = request.data["status"]
        order.save()
        return Response(
            {"message": f"Order {order.id} updated successfully"},
            status=status.HTTP_200_OK,
        )
    return Response(
        {"message": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


# Customers can browse all categories
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_categories(request):
    if request.method == "GET":
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(
        {"message": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


# Customers can browse all the menu items at once
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_menu_items(request):
    if request.method == "GET":
        menu_items = MenuItem.objects.all()
        serializer = MenuItemSerializer(menu_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(
        {"message": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )


class MenuItemView(generics.RetrieveUpdateDestroyAPIView):
    # queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    paginate_by = 5
    ordering = "price"

    def is_customer(self, request):
        return request.user.groups.filter(name="customers").exists()

    def is_crew(self, request):
        return request.user.groups.filter(name="crew").exists()

    def is_manager(self, request):
        return request.user.groups.filter(name="managers").exists()

    def get_permissions(self):
        if self.is_customer(self.request):
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.is_crew(self.request):
            self.permission_classes = [permissions.IsAuthenticated, IsCrew]
        elif self.is_manager(self.request):
            self.permission_classes = [permissions.IsAuthenticated, IsManager]
        return super().get_permissions()

    def get_queryset(self):
        menu_items = MenuItem.objects.all()
        if self.request.GET.get("category"):
            category = self.request.GET.get("category")
            menu_items = menu_items.filter(category=category)
        if (
            self.request.GET.get("ordering")
            and self.request.GET.get("ordering") == "price"
        ):
            menu_items = menu_items.order_by("price")
        return menu_items


# Customers can place orders and Customers can browse their own orders
class OrderView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


# Customers can access previously added items in the cart
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_cart(request):
    if request.method == "GET":
        cart = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(
        {"message": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
    )
