from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import TopUpForm
from .models import Wallet
from .services import WalletService


@login_required
def wallet_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = TopUpForm(request.POST)
        if form.is_valid():
            try:
                WalletService.top_up(user=request.user, amount=form.cleaned_data["amount"])
            except ValueError:
                messages.error(request, "این مبلغ با سقف مجاز کیف پول سازگار نیست.")
            else:
                messages.success(request, "موجودی کیف پول با موفقیت افزایش یافت.")
        else:
            messages.error(request, "یک مبلغ مثبت و معتبر وارد کنید.")
        return redirect("wallet:detail")

    return render(request, "wallet/detail.html", {"wallet": wallet, "top_up_form": TopUpForm()})
