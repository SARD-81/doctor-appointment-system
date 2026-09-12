from decimal import Decimal, InvalidOperation

from django.contrib import messages
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
            messages.success(request, "کیف پول شما با موفقیت شارژ شد.")
        except (TypeError, ValueError, InvalidOperation):
            messages.error(request, "مبلغ وارد شده معتبر نیست.")
        return redirect("wallet:detail")

    return render(request, "wallet/detail.html", {"wallet": wallet})
