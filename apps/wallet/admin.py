from django.contrib import admin
from apps.wallet.models import Wallet, WalletTransaction


class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    can_delete = False
    readonly_fields = ("transaction_type", "amount", "created_at")
    fields = ("transaction_type", "amount", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "balance", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [WalletTransactionInline]
    ordering = ("-created_at",)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "wallet", "get_user", "transaction_type", "amount", "created_at")
    list_filter = ("transaction_type", "created_at")
    search_fields = (
        "wallet__user__username",
        "wallet__user__email",
    )
    autocomplete_fields = ("wallet",)
    list_select_related = ("wallet__user",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    @admin.display(description="کاربر", ordering="wallet__user")
    def get_user(self, obj):
        return obj.wallet.user
