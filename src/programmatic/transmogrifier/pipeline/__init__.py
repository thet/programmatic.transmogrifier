# For some reason, I had to patch VirtualHostMonster.
# Reason is some other package.
# This hack is ugly, like the error it fixes.
###
# Don't include this package in production.
###
from Products.SiteAccess import VirtualHostMonster as vhm
from zExceptions import BadRequest
import logging

logger = logging.getLogger(name='programmatic.transmogrifier VHM patch')
orig_VirtualHostMonster = vhm.VirtualHostMonster


class VirtualHostMonster(orig_VirtualHostMonster):
    def manage_afterAdd(self, item, container):
        try:
            super(VirtualHostMonster, self).manage_afterAdd(item, container)
        except BadRequest:
            logger.warn('ignored: "BadRequest: This container already has a Virtual Host Monster"')  # noqa
            return
vhm.VirtualHostMonster = VirtualHostMonster
