# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from transmogrifier.programmatic.testing import TRANSMOGRIFIER_PROGRAMMATIC_INTEGRATION_TESTING  # noqa
from plone import api

import unittest


class TestSetup(unittest.TestCase):
    """Test that transmogrifier.programmatic is properly installed."""

    layer = TRANSMOGRIFIER_PROGRAMMATIC_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if transmogrifier.programmatic is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'transmogrifier.programmatic'))


class TestUninstall(unittest.TestCase):

    layer = TRANSMOGRIFIER_PROGRAMMATIC_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        self.installer.uninstallProducts(['transmogrifier.programmatic'])

    def test_product_uninstalled(self):
        """Test if transmogrifier.programmatic is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'transmogrifier.programmatic'))
