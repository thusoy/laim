import pwd
import os


class Laim:
    def __init__(self):
        drop_privileges()


def drop_privileges(user='laim'):
    pwd_details = pwd.getpwnam(user)

    # Remove group privileges
    os.setgroups([])

    os.setgid(pwd_details.pw_gid)
    os.setuid(pwd_details.pw_uid)
