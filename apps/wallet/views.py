from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import TopUpForm
from .models import Wallet
from .services import WalletService


def _get_or_repair_wallet(user):
    try:
        wallet, _ = Wallet.objects.get_or_create(user=user)
    except InvalidOperation:
        Wallet.objects.filter(user=user).update(balance=Decimal("0.00"))
        wallet = Wallet.objects.get(user=user)
    return wallet


@login_required
def wallet_view(request):
    wallet = _get_or_repair_wallet(request.user)
    form = TopUpForm()

    if request.method == "POST":
        form = TopUpForm(request.POST)
        if form.is_valid():
            try:
                WalletService.top_up(
                    user=request.user, amount=form.cleaned_data["amount"]
                )
            except (TypeError, ValueError):
                messages.error(request, "موجودی کیف پول به سقف مجاز رسیده است.")
                return redirect("wallet:detail")
            messages.success(request, "کیف پول شما با موفقیت شارژ شد.")
            return redirect("wallet:detail")

    return render(
        request,
        "wallet/detail.html",
        {"wallet": wallet, "amount_form": form},
    )
