from django.contrib import admin

from .models import Wallet, WalletTransaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "updated_at")
    search_fields = ("user__email",)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "transaction_type", "amount", "balance_after", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("wallet__user__email",)
