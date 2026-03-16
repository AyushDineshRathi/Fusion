import sys
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation

def check_user(username):
    u = User.objects.filter(username=username).first()
    if not u:
        print(f"User {username} not found")
        return
    print(f"User {username}:")
    print(f"  is_active: {u.is_active}")
    print(f"  check_password: {u.check_password('student123') if 'bsm' in username or 'bcs' in username else u.check_password('faculty123')}")
    
    ext = ExtraInfo.objects.filter(user=u).first()
    if ext:
        print(f"  ExtraInfo: {ext.user_type}")
    else:
        print("  ExtraInfo: Missing")
        
    holds = HoldsDesignation.objects.filter(user=u)
    print(f"  Designations: {[h.designation.name for h in holds]}")

check_user('23bsm001')
check_user('faculty1')
