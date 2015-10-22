# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import transmogrifier.programmatic


class TransmogrifierProgrammaticLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=transmogrifier.programmatic)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'transmogrifier.programmatic:default')


PROGRAMMATIC_TRANSMOGRIFIER_FIXTURE = TransmogrifierProgrammaticLayer()


PROGRAMMATIC_TRANSMOGRIFIER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PROGRAMMATIC_TRANSMOGRIFIER_FIXTURE,),
    name='TransmogrifierProgrammaticLayer:IntegrationTesting'
)


PROGRAMMATIC_TRANSMOGRIFIER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PROGRAMMATIC_TRANSMOGRIFIER_FIXTURE,),
    name='TransmogrifierProgrammaticLayer:FunctionalTesting'
)


PROGRAMMATIC_TRANSMOGRIFIER_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PROGRAMMATIC_TRANSMOGRIFIER_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name='TransmogrifierProgrammaticLayer:AcceptanceTesting'
)
