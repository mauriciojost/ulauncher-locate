import os
import logging
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

from locale import atof, setlocale, LC_NUMERIC
from gi.repository import Notify
from itertools import islice
from subprocess import Popen, PIPE, check_call, CalledProcessError
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.OpenAction import OpenAction


logger = logging.getLogger(__name__)
ext_icon = 'images/icon.png'
exec_icon = 'images/executable.png'
dead_icon = 'images/dead.png'

action_update = 'U'
action_locate = 'L'

database_filepath = os.path.join(os.getenv("HOME"), '.locate-ulauncher-database')




class LocateExtension(Extension):

    def __init__(self):
        super(LocateExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        setlocale(LC_NUMERIC, '')  # set to OS default locale;

    def show_notification(self, title, text=None, icon=ext_icon):
        logger.debug('Show notification: %s' % text)
        icon_full_path = os.path.join(os.path.dirname(__file__), icon)
        Notify.init("LocateExtension")
        Notify.Notification.new(title, text, icon_full_path).show()


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        pattern = str(event.get_argument())
        keyword = event.get_keyword()
        
        for pref_id, pref_value in list(extension.preferences.items()):
            if pref_value == keyword:
                keyword_id = pref_id
            elif pref_id == 'flags':
                locate_flags = pref_value

        if keyword_id == "locate":
            # locate a file in database
            return RenderResultListAction(list(islice(self.generate_results(extension, pattern, locate_flags), 15)))
        elif keyword_id == "update":
            # update files database
            self.update(extension)
            return DoNothingAction()

    def update(self, extension):
        update_database(extension)

    def generate_results(self, extension, pattern, locate_flags):
        for (f) in get_file_list(extension, pattern, locate_flags):
            path = '%s' % (f)
            yield ExtensionSmallResultItem(icon=exec_icon,
                                           name=path,
                                           on_enter=OpenAction(path))


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_data()
        self.open(extension, data['path'])

    def open(self, extension, path):
        cmd = ['open', path]
        logger.info(' '.join(cmd))

        try:
            check_call(cmd) == 0
            extension.show_notification("Done", "File %s open" % path, icon=dead_icon)
        except CalledProcessError as e:
            extension.show_notification("Error", "code %s" % e.returncode)
        except Exception as e:
            logger.error('%s: %s' % (type(e).__name__, e))
            extension.show_notification("Error", "Check the logs")
            raise


def get_file_list(extension, pattern, flags):
    """
    Returns a list filenames.
    """
    cmd = ['locate', '--database', database_filepath]

    for flag in flags.split(' '):
        cmd.append(flag)

    cmd.append(pattern)

    logger.debug('Locating files with pattern: %s ' % (','.join(cmd)))

    process = Popen(cmd, stdout=PIPE)
    out = process.communicate()[0].decode('utf8')
    for line in out.split('\n'):
        f = line
        yield (f)

def update_database(extension):
    """
    Update the database.
    """
    cmd = ['updatedb', '--require-visibility', '0', '--output', database_filepath]

    logger.debug('Updating database: %s ' % (','.join(cmd)))

    try:
        check_call(cmd) == 0
        extension.show_notification("Done", "It's updated now", icon=dead_icon)
    except CalledProcessError as e:
        extension.show_notification("Error", "'updatedb' returned code %s" % e.returncode)
    except Exception as e:
        logger.error('%s: %s' % (type(e).__name__, e))
        extension.show_notification("Error", "Check the logs")
        raise

if __name__ == '__main__':
    LocateExtension().run()
