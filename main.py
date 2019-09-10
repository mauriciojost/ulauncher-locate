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
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction


logger = logging.getLogger(__name__)
ext_icon = 'images/icon.png'
exec_icon = 'images/executable.png'
dead_icon = 'images/dead.png'
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
            elif pref_id == 'locate_flags':
                locate_flags = pref_value
            elif pref_id == 'open_script':
                open_script = pref_value

        if keyword_id == "locate_keyword":
            # locate a file in database
            return RenderResultListAction(list(islice(self.generate_results(extension, pattern, locate_flags, open_script), 100)))
        elif keyword_id == "update_keyword":
            # update files database
            cmd = ' '.join(['updatedb', '--require-visibility', '0', '--output', database_filepath])
            logger.debug('Database update command: %s ' % cmd)
            return RunScriptAction(cmd)

    def generate_results(self, extension, pattern, locate_flags, open_script):
        for (f) in get_file_list(extension, pattern, locate_flags):
            path = '%s' % (f)
            script = open_script + ' ' + path
            yield ExtensionSmallResultItem(icon=exec_icon, name=path, on_enter=RunScriptAction(script))


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        logger.debug('Ignored')


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

if __name__ == '__main__':
    LocateExtension().run()
