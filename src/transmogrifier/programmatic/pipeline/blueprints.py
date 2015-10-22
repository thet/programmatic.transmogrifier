# -*- coding: utf-8 -*-
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from collective.geolocationbehavior.geolocation import IGeolocatable
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import traverse
from datetime import date
from geopy.geocoders import Nominatim
from plone.event.utils import pydt
from plone.formwidget.geolocation.geolocation import Geolocation
from zope.interface import classProvides
from zope.interface import implements
import logging
import re

logger = logging.getLogger("transmogrifier.programmatic typemapper")

# TODO:
# OK # * excludeFromNav
# OK # * exclude lineage_registry
# * activate subsites
# OK # * keep UIDs

# * set default pages in 2nd run
# * set Subjects
# * fix image urls in texts:
#       http://goetzis.programmatic.pro/kultur-freizeit-sport/sport-und-freizeitanlagen/sport-und-freizeitanlagen/resolveuid/6f31a37c43a04ab3b3200f2c322b1352/image_portlet-links
#       http://goetzis.programmatic.pro/kultur-freizeit-sport/sport-und-freizeitanlagen
#       http://goetzis.programmatic.pro/ortsportrait/tourismusinfo


USER_MAP = {}
TRANSITION_MAP = {
    'reject': 'make-private',
    'retract': 'make-private',
    'submit': 'make-internal',
    'hide': 'make-private',
    'show': 'make-internal',
    'publish': 'make-external',
    'publishToMain': 'make-mainportal',
    'retractFromMain': 'make-external'
}
STATES_TO_TRANSITION_MAP = {
    'confidential': 'make-private',
    'pending': 'make-internal',
    'private': 'make-private',
    'published': 'make-external',
    'studentshare': 'make-private',
    'visible': 'make-internal',

    # intranet
    'external': 'make-external',
    'internal': 'make-internal',
    'internally_published': 'make-internal',

    # team membership
    # paper workflow
    # psc
    # helpcenter
    'accepted': 'make-internal',
    'alpha': 'make-internal',
    'being-discussed': 'make-internal',
    'beta': 'make-internal',
    'closed': 'make-private',
    'completed': 'make-internal',
    'deferred': 'make-internal',
    'draft': 'make-internal',
    'final': 'make-internal',
    'hidden': 'make-private',
    'in-progress': 'make-internal',
    'inactive': 'make-private',
    'obsolete': 'make-private',
    'pre-release': 'make-internal',
    'ready-for-merge': 'make-internal',
    'rejected': 'make-private',
    'release-candidate': 'make-internal',
    'unapproved': 'make-private',

    # member approval workflow / member auto workflow
    'disabled': 'make-private',
    'new': 'make-internal',
    'new_private': 'make-private',
    'public': 'make-internal',

    # ploneboard
    'initial': 'make-internal',
    'rejected': 'make-private',
    'retracted': 'make-private',
    'active': 'make-internal',
    'locked': 'make-internal',
    'freeforall': 'make-internal',
    'memberposting': 'make-internal',
    'moderated': 'make-internal',
}
LAYOUT_MAP = {
    'ak_summary_view': 'summary_view',
    'detail-view': 'newsitem_view',
    'news-index': 'summary_view',
    # addons
    'galleryview': 'album_view',
    'venue': 'venue_view',
    # webmeisterei indexes
    'base_view': 'contact_view',
    'company_view': 'contact_view',
    'companyindex': 'contact_listing',
    'companyindex_open': 'contact_listing',
    'contactform': 'view',
    'index-tile-view': 'contact_listing',
    'item-index': 'contact_listing',
    'staffindex': 'contact_listing',
    'view-person': 'contact_view',
    'view_company': 'contact_view',
    # plone.app.contenttypes changes
    'all_content': 'full_view',
    'atct_album_view': 'album_view',
    'collection_view': 'listing_view',
    'folder_album_view': 'album_view',
    'folder_full_view': 'full_view',
    'folder_listing': 'listing_view',
    'folder_summary_view': 'summary_view',
    'folder_tabular_view': 'tabular_view',
    'standard_view': 'listing_view',
    'thumbnail_view': 'album_view',
    'view': 'listing_view',
}
IMAGE_SCALE_MAP = {
    'icon': 'icon',
    'large': 'large',
    'listing': 'listing',
    'mini': 'mini',
    'preview': 'preview',
    'thumb': 'thumb',
    'tile': 'tile',
    # BBB
    'article': 'preview',
    'artikel': 'preview',
    'carousel': 'preview',
    'company_index': 'thumb',
    'content': 'preview',
    'leadimage': 'tile',
    'portlet-fullpage': 'large',
    'portlet-halfpage': 'large',
    'portlet-links': 'thumb',
    'portlet': 'thumb',
    'staff_crop': 'thumb',
    'staff_index': 'thumb',
}


DEFAULT_COUNTRY = "040"  # Austria
LOC_MAP = {}


def wiki_to_structured(text):
    """Example text:
    [[text]]
    [text with space]
    CamelCase

    >>> from iaem.site.migrate21.blueprints import wiki_to_structured as ws
    >>> txt = "Wer regiert das Internet ? 1244 aha bla - bla~!"
    >>> ws('[[%s]]' % txt)
    '"WerRegiertDasInternet1244AhaBlaBla":WerRegiertDasInternet1244AhaBlaBla'

    >>> txt = "KNM Was ist das ?"
    >>> ws('[[%s]]' % txt)
    '"KNMWasIstDas":KNMWasIstDas'

    >>> ws(" * KlangKunst Geschichte und Beispiele")
    ' * "KlangKunst":KlangKunst Geschichte und Beispiele'
    >>> ws(" * !KlangKunst Geschichte und Beispiele")
    ' * !KlangKunst Geschichte und Beispiele'
    >>> ws(" * [[Klang Kunst]] Geschichte und Beispiele")
    ' * "KlangKunst":KlangKunst Geschichte und Beispiele'
    >>> ws(" * [Klang Kunst] Geschichte und Beispiele")
    ' * "KlangKunst":KlangKunst Geschichte und Beispiele'

    With the help of:
        http://stackoverflow.com/a/1128326/1337474
        http://stackoverflow.com/a/5843547/1337474
    """

    def _link_alphanumeric(matchob):
        """E.g.
        >>> _strip_nonalpha('Super duper 322 ?!- aha')
        'SuperDuper322Aha'
        """
        match = matchob.group(0)
        text = safe_unicode(match)
        # Capitalize without title() to keep all uppercase as is.
        text = u' '.join([
            u'{}{}'.format(
                s[0].upper() if s else '',
                s[1:] if len(s) > 1 else ''
            ) for s in text.split(' ')
        ])
        text = re.sub('[^A-Za-z0-9]+', '', text)
        return r'"{}":{}'.format(text, text)

    #                v selects at least an empty space
    text = re.sub(r'[^!](([A-Z][a-z|0-9]+){2,})', r' "\1":\1', text)  # CmlCs, excpet starts with !  # noqa
    text = re.sub(r'\[\[(.*)\]\]', _link_alphanumeric, text)  # replace [[]]
    text = re.sub(r'\[(.*)\]', _link_alphanumeric, text)  # replace []
    return text


def cleanup_text(text):
    """Cleanup the text from unnecessary input.

    Replace all empty paragraphs.

    regexpal regex: <p[^>]*?>(\s|<br>|<br/>)*?</p>

    regexpal.com test data:

    <p></p>sadasd
    asdasd
    <p class="some"></p>
    bla
    <p> </p>
    aha
    <p>
    </p>
    kloa
    <p>

    <br/><br>

    </p>

    <p>not me<br/>   </p>
    jo

    """
    # Remove empty paragraphs
    text = re.sub(r'<p[^>]*?>(\s|<br>|<br/>|<br />|\xc2\xa0)*?</p>', '', text,
                  flags=re.UNICODE)
    return text


def transition_fixer(item):
    """Remap transitions, loose workflow history (don't need it) and prepare
    for plone.app.transmogrifier workflowupdater (instead of
    collective.jsonmigrator's)
    """
    for _workflow, _transitions in item.get('_workflow_history', {}).items():
        # remove null actions
        _transitions = [it for it in _transitions if it.get('action')]
        # sort after date
        _transitions = sorted(
            _transitions,
            cmp=lambda x, y: cmp(DateTime(x['time']), DateTime(y['time']))
        )
        action = None
        if _transitions:
            # Get last transition action
            action = _transitions[-1].get('action')
        if action:
            # Remap the transition action to new workflow
            _action = TRANSITION_MAP.get(action, action)
            item['_transitions'] = (_action, )
            logger.debug("changed transition from {} to {}".format(
                action, _action))
    return item


def state_fixer(item):
    """Since there are some state changes without transitions, remap states to
    transitions.
    """
    for _workflow, _transitions in item.get('_workflow_history', {}).items():
        # sort after date
        _transitions = sorted(
            _transitions,
            cmp=lambda x, y: cmp(DateTime(x['time']), DateTime(y['time']))
        )
        last_workflow_change = _transitions[-1]
        last_state = last_workflow_change.get('review_state')
        if last_state:
            action = STATES_TO_TRANSITION_MAP[last_state]
            item['_transitions'] = (action, )
            logger.debug(
                "changed workflow to state {} via transition {}".format(
                    last_state, action
                )
            )
    return item


def user_fixer(item):
    """Map old usernames to new.
    """
    owner = item.get('_owner')
    if owner in USER_MAP:
        _owner = USER_MAP[owner]
        item['_owner'] = _owner
        logger.debug("changed owner from {} to {}".format(owner, _owner))

    creators = item.get('creators', [])
    _creators = [USER_MAP.get(it, it) for it in creators]
    item['creators'] = _creators
    logger.debug("changed creators from {} to {}".format(creators, _creators))

    return item


def image_scale_fixer(text):

    if text:
        for old, new in IMAGE_SCALE_MAP.items():
            # replace plone.app.imaging scales
            text = text.replace(
                '@@images/image/{0}'.format(old),
                '@@images/image/{0}'.format(new)
            )
            # replace AT traversing scales
            text = text.replace(
                'image_{0}'.format(old),
                '@@images/image/{0}'.format(new)
            )

    return text


def localroles_fixer(item):
    """Fixup local roles. Give owners supplementary rights. fixup the username.
    Must run before user_fixer.
    """

    local_roles = item.get('_ac_local_roles', {})
    _local_roles = {}
    owner = item.get('_owner')
    if local_roles:
        for key, val in local_roles.items():

            if key != owner and 'Owner' in val:
                # Fix non-owners having the owner role
                val.remove('Owner')
                if 'Reader' not in val:
                    val.append('Reader')
                if 'Editor' not in val:
                    val.append('Editor')
                if 'Contributor' not in val:
                    val.append('Contributor')
                if 'Reviewer' not in val:
                    val.append('Reviewer')
                logger.debug(
                    "replaced owner role in localroles for {}".format(key))

            if key in USER_MAP:
                # Fix changed username
                _key = USER_MAP[key]
                logger.debug(
                    "replaced owner name in localroles from {} to {}".format(
                        key, _key))
                key = _key

            _local_roles[key] = val

    item['_ac_local_roles'] = _local_roles
    return item


def layout_mapper(item):

    layout = item.get('_layout')
    if layout and layout in LAYOUT_MAP.keys():
        item['_layout'] = LAYOUT_MAP[layout]

    return item


class CatalogSource(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        self.portal_type = options.get('portal_type')

    def __iter__(self):
        for item in self.previous:
            yield item

        cat = getToolByName(self.context, 'portal_catalog')
        query = {}
        query['portal_type'] = self.portal_type
        res = cat.searchResults(**query)

        for item in res:
            yield item


class TypeMapper(object):
    """Maps obsolete types to new ones.
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        self.ignore_path = options.get('ignore_path')
        self.only_path = options.get('only_path')

    @property
    def type_map(self):

        event_map = {
            'type': 'Event',
            'attributes': {
                'startDate': 'start',
                'endDate': 'end',
                'wholeDay': 'whole_day',
                'openEnd': 'open_end',
                # 'recurrence': 'recurrence',
                'location': 'location_uid',
                # 'attendees': 'attendees',
                # 'location_notes': 'location_notes',
                'contactName': 'contact_name',
                'contactEmail': 'contact_email',
                'contactPhone': 'contact_phone',
                'eventUrl': 'event_url',
                'eventUid': 'sync_uid',
                # 'text': 'text'
            }
        }

        type_map = {
            # STDTYPES
            'Collection': 'Collection',
            'Document': 'Document',
            'Event': event_map,
            'File': 'File',
            'Folder': 'Folder',
            'Folderish Document': 'Document',
            'Folderish Event': event_map,
            'Folderish News Item': 'News Item',
            'Image': 'Image',
            'Link': 'Link',
            'News Item': 'News Item',
            # ADDONS
            'AKEvent': event_map,  # TODO: ticketshops, Venues
            'AKNewsItem': 'News Item',  # TODO: attachement

            'TicketShop': 'Venue',
            'Venue': 'Venue',
            'Ticket': 'Ticket',
            'Ticket Occurrence': 'Ticket Occurrence',

            # STDTYPES
            'Company': {'type': 'Company', 'attributes': {
                # 'title': 'title',
                # 'description': 'description',
                'contact': 'last_name',
                # 'street': 'street',
                'zip': 'zip_code',
                # 'city': 'city',
                # 'phone': 'phone',
                # 'fax': 'fax',
                # 'email': 'email',
                'homepage': 'website',
                'banner': 'image',
                'opened': 'text',
                'subjects': 'categories'  # NOTE: we're mapping subject to subjects below. originally, this comes as subject.  # noqa
            }},
            'Company Folder': 'Folder',
            'Staff Folder': 'Folder',
            'Staff Person': {'type': 'Person', 'attributes': {
                # 'title': 'title',
                # 'description': 'description',
                'firstName': 'first_name',
                'lastName': 'last_name',
                'academicTitle': 'academic_title',
                # 'street': 'street',
                'zip': 'zip_code',
                # 'city': 'city',
                # 'phone': 'phone',
                # 'mobile': 'mobile',
                # 'fax': 'fax',
                # 'email': 'email',
                'web': 'website',
                'banner': 'image',
                'opened': 'text',
                'subjects': 'categories'
            }},

            # TODO
            # 'Ticket': 'Ticket',
            # 'Ticket Occurrence': 'Ticket Occurrence',

            # ADDONS
            'CMFPhoto': 'Image',
            'CMFPhotoAlbum': 'Folder',
            'Wiki Page': {'type': 'Document', 'attributes': {'document_src': 'text'}},  # noqa
            'PloneboardComment': 'Document',
            'PloneboardConversation': 'Document',
            'PloneboardForum': {'type': 'Document', 'attributes': {'category': 'subjects'}},  # noqa  # note: subject on context, subjects on behavior
        }
        return type_map

    def item_manipulator(self, item):
        type_map = self.type_map

        old_type = item['_type']
        repl_type = type_map[old_type]

        if old_type == "Wiki Page":
            # "document_src" is copied to "text"
            # text/structured works OK with wiki pages
            item['_content_type_text'] = 'text/structured'
            item['document_src'] = wiki_to_structured(item['document_src'])

        # Prepare structure
        if not isinstance(repl_type, dict):
            repl_type = {'type': repl_type}

        if 'attributes' not in repl_type:
            repl_type['attributes'] = {}

        # Standard AT to DX replacements
        repl_type['attributes'].update({
            'effectiveDate': 'effective_date',
            'expirationDate': 'expiration_date',
            'excludeFromNav': 'exclude_from_nav',
            'allowDiscussion': 'allow_discussion',
        })

        if not item.get('title', False):
            # Set the title to the id for items without title
            item['title'] = item['_id']

        # map subject to subjects, which is the behavior field name in
        # dexterity. it's stored on the subjec attribute on the context.
        if item.get('subject', False):
            # Add subjects
            subjects = item.get('subject', ())
            if subjects:
                item['subjects'] = tuple(subjects)
            del item['subject']

        # MAPPING

        if 'type' in repl_type:
            # replace type
            item['_type'] = repl_type['type']

        for oldname, newname in repl_type['attributes'].items():
            # Move old attribute to new name

            if oldname in item:

                val = item.get(oldname, None)
                if val in (None, 'None'):
                    # Don't migrate, if item is None (or 'None')
                    del item[oldname]
                    continue

                if newname in ('date',):
                    DT = DateTime(val)
                    val = date(DT.year(), DT.month(), DT.day())

                if newname in ('effective_date', 'expiration_date'):
                    if val:
                        try:
                            val = DateTime(val)
                        except:
                            del item[oldname]
                            continue

                if newname in ('start', 'end'):
                    if val:
                        try:
                            DT = DateTime(val)
                            val = pydt(DT)
                        except:
                            del item[oldname]
                            continue

                if item.get(newname, False):
                    # append if not empty
                    newval = item[newname]
                    if isinstance(newval, basestring):
                        # Prepend the old fieldname if is isn't a
                        # plain text field
                        if newname == 'text' and oldname not in (
                            'text', 'document_src'
                        ):
                            item[newname] = u'{}\n\n{}: {}'.format(
                                newval,
                                oldname,
                                val
                            )
                        else:
                            item[newname] = u'{}\n\n{}'.format(
                                newval,
                                val
                            )

                    elif isinstance(newval, list)\
                            or isinstance(newval, tuple):
                        item[newname] = newval + val

                    elif isinstance(newval, dict)\
                            and isinstance(val, dict):
                        item[newname].update(val)

                    else:
                        # don't append
                        item[newname] = val

                else:
                    if newname == 'text' and oldname not in (
                        'text', 'document_src'
                    ):
                        # IAEM specific
                        # Prepend the old fieldname if is isn't a
                        # plain text field
                        item[newname] = u'{}: {}'.format(
                            oldname,
                            val
                        )
                    else:
                        item[newname] = val

                # Delete old field from item - we don't want to
                # import it twice.
                del item[oldname]

        # fix image scale names and urls
        text = item.get('text')
        if text:
            item['text'] = cleanup_text(image_scale_fixer(text))

        if item['_type'] in ('Person', 'Company', 'Organization'):
            street = item.get('street', None)
            if street:
                address = ' '.join([it for it in [
                    street,
                    item.get('zip_code', None),
                    item.get('city', None),
                ] if it]).strip()
                item['country'] = DEFAULT_COUNTRY
                latlng = (None, None)
                if address in LOC_MAP:
                    latlng = LOC_MAP[address]
                else:
                    try:
                        geolocator = Nominatim()
                        location = geolocator.geocode(address)
                        if location:
                            latlng = (location.latitude, location.longitude)
                            LOC_MAP[address] = latlng
                    except:
                        # Might have been network timeout. so what..?
                        pass

                if latlng[0] and latlng[1]:
                    item['latitude'] = latlng[0]
                    item['longitude'] = latlng[1]

        if item['_type'] == 'File':
            # File fixups
            datafield = item.get('_datafield_file', None)
            if datafield:
                # assert(datafield['encoding'])  # declared encoding (base64)

                if datafield['content_type'].startswith('image'):
                    # Change all image files to image types
                    item['_type'] = 'Image'
                    item['_datafield_image'] = datafield
                    del item['_datafield_file']
            else:
                # File without content?
                return None

        item = state_fixer(item)
        item = layout_mapper(item)
        # item = localroles_fixer(item)  # must run before user_fixer
        # item = user_fixer(item)

        logger.debug(
            'Type mapped item {} from oldtype {} to newtype {}.'.format(
                item.get('_path'),
                old_type,
                item.get('_type')
            )
        )

        return item

    def __iter__(self):
        type_map = self.type_map

        for item in self.previous:

            if self.ignore_path and self.ignore_path in item['_path']:
                continue

            if self.only_path and self.only_path not in item['_path']:
                continue

            if item['_type'] not in type_map.keys():
                continue

            item = self.item_manipulator(item)

            if item:
                yield item
            else:
                continue


class LatLngUpdater(object):
    """Sets collective.geolocationbehavior on the item.
    """
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

    def __iter__(self):

        for item in self.previous:

            if item['_type'] in ('Person', 'Company', 'Organization', 'Venue'):

                latitude = item.get('latitude', None)
                longitude = item.get('longitude', None)
                if latitude is None or longitude is None:
                    # not enough information
                    yield item
                    continue

                path = item['_path']
                # path = path.replace('/plone', '')  # not necessary
                ob = traverse(self.context, str(path).lstrip('/'), None)
                if ob is None:
                    yield item
                    continue  # object not found

                geo = IGeolocatable(ob)
                geo.geolocation = Geolocation(
                    latitude=latitude, longitude=longitude)

            yield item


class RemoveCreator(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context
        self.remove_name = options.get('remove_name')

    def __iter__(self):

        for item in self.previous:
            path = item['_path']
            ob = traverse(self.context, str(path).lstrip('/'), None)
            if ob is None:
                yield item
                continue  # object not found

            rm_name = self.remove_name
            creators = ob.creators
            if len(creators) > 1 and rm_name in creators:
                creators = tuple([it for it in creators if it != rm_name])
                ob.creators = creators

            yield item


class StateFixer(object):
    classProvides(ISectionBlueprint)
    implements(ISection)

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.context = transmogrifier.context

    def __iter__(self):

        for item in self.previous:
            item = state_fixer(item)
            yield item
