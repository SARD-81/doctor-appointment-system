from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Wallet
from .services import WalletService


@login_required
def wallet_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get("amount", "0"))
            WalletService.top_up(user=request.user, amount=amount)
        except (ValueError, InvalidOperation):
            pass
        return redirect("wallet:detail")

    return render(request, "wallet/detail.html", {"wallet": wallet})
