programmatic.transmogrifier
===========================

Basic transmogrifier pipeline to migrate plone sites from collective.jsonify created sources.


1) Export content via collective.jsonify from the Plone source site.
Install following these instructions: https://github.com/collective/collective.jsonify/blob/master/docs/install.rst
Export content by using the exporter: https://github.com/collective/collective.jsonify/blob/master/docs/install.rst#using-the-exporter

2) Import by using mr.migrator into the Plone target site.
Open the ``@@mr.migrator`` on your Plone site root, select a pipeline and run it. Start by using the
"programmatic.transmogrifier - 1 - migrate content: migrate main content" pipeline and then the
"programmatic.transmogrifier - 2 - migration postwork: fix layout, add lat/lng, remove admin creator, fix dates".

Done.
If you forgot simething important, you can create another pipeline using blueprints which modify existing content or create new one. This workflow is fine, as long the site structure isn't changed.
