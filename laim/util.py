import os
import pwd


def drop_privileges(user):
    pwd_details = pwd.getpwnam(user)

    # Remove group privileges
    os.setgroups([])

    os.setgid(pwd_details.pw_gid)
    os.setuid(pwd_details.pw_uid)
