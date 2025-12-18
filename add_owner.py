import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','koki_foodhub.settings')
django.setup()
from django.contrib.auth.models import User, Group
def promote_owners_to_admin():
    owner_group, _ = Group.objects.get_or_create(name='Owner')
    admin_group, _ = Group.objects.get_or_create(name='Admin')

    owners = User.objects.filter(groups=owner_group)
    if not owners.exists():
        print('No users found in Owner group.')
        return

    for u in owners:
        changed = False
        if admin_group not in u.groups.all():
            u.groups.add(admin_group)
            changed = True
        if not u.is_staff:
            u.is_staff = True
            changed = True
        if changed:
            u.save()
            print(f"Promoted {u.username}: added to Admin group and set is_staff=True")
        else:
            print(f"No change for {u.username}: already promoted")


if __name__ == '__main__':
    promote_owners_to_admin()
