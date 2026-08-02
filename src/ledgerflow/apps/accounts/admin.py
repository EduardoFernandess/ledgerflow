from django.contrib import admin

from ledgerflow.apps.accounts.models import Membership, Organization, User

admin.site.register(User)
admin.site.register(Organization)
admin.site.register(Membership)
