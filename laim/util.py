import os
import pwd
import re


def drop_privileges(user):
    pwd_details = pwd.getpwnam(user)

    # Remove group privileges
    os.setgroups([])

    os.setgid(pwd_details.pw_gid)
    os.setuid(pwd_details.pw_uid)


def unfold(folded):
    '''Helper to unfold headers'''
    if folded is None:
        return None
    return re.sub(r'\r?\n ', ' ', folded)
