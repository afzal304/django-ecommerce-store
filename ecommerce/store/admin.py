from django.contrib import admin
from .models import * 
from django.utils.html import format_html

# -------------------------
# Customer
# -------------------------
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'email')
admin.site.register(Customer, CustomerAdmin)

# -------------------------
# Product Images Inline
# -------------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 80px; height:auto;" />', obj.image.url)
        return ""
admin.site.register(ProductImage)

# -------------------------
# Variants Inline
# -------------------------
class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    fields = ("color", "size", "price", "stock")
    show_change_link = True


class ProductAdmin(admin.ModelAdmin):
    list_display = ('category','name','price','digital','image','description','stock')
    inlines = [ProductImageInline,VariantInline]  # ✅ show extra images inline
    #search_fields = ('name', 'category__name')
    list_filter = ('category',)

    def description(self, obj):
        return (obj.description[:50] + "...") if obj.description else "-"
        description.description = "Description"
admin.site.register(Product,ProductAdmin)

# -------------------------
# Variant (standalone admin too)
# -------------------------
class VariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'size', 'price', 'stock')
    list_filter = ('color', 'size')
    search_fields = ('product__name', 'color', 'size')
admin.site.register(Variant, VariantAdmin)

# -------------------------
# Order ItemInline
# -------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product','variant','quantity','date_added')
    can_delete = False

# -------------------------
# Order
# -------------------------
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'session_key', 'date_ordered', 'complete', 'transaction_id')
    inlines = [OrderItemInline]
admin.site.register(Order, OrderAdmin)

# -------------------------
# Order Item
# -------------------------
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'variant', 'order', 'quantity', 'date_added')
admin.site.register(OrderItem, OrderItemAdmin)

# -------------------------
# Shipping
# -------------------------
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('customer', 'order', 'address', 'city', 'state', 'zipcode', 'date_added')
admin.site.register(ShippingAddress, ShippingAddressAdmin)

# -------------------------
# Category
# -------------------------
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
admin.site.register(Category, CategoryAdmin)