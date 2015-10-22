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


TRANSMOGRIFIER_PROGRAMMATIC_FIXTURE = TransmogrifierProgrammaticLayer()


TRANSMOGRIFIER_PROGRAMMATIC_INTEGRATION_TESTING = IntegrationTesting(
    bases=(TRANSMOGRIFIER_PROGRAMMATIC_FIXTURE,),
    name='TransmogrifierProgrammaticLayer:IntegrationTesting'
)


TRANSMOGRIFIER_PROGRAMMATIC_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(TRANSMOGRIFIER_PROGRAMMATIC_FIXTURE,),
    name='TransmogrifierProgrammaticLayer:FunctionalTesting'
)


TRANSMOGRIFIER_PROGRAMMATIC_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        TRANSMOGRIFIER_PROGRAMMATIC_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE
    ),
    name='TransmogrifierProgrammaticLayer:AcceptanceTesting'
)
