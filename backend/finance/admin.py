from django.contrib import admin
from .models import PaymentClaim

@admin.register(PaymentClaim)
class PaymentClaimAdmin(admin.ModelAdmin):
    list_display = ('contract', 'amount', 'status', 'claim_date')
    list_filter = ('status',)
