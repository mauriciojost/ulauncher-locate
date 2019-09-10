import os
import logging
import gi
import mimetypes

gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk, Gio, Notify
from subprocess import Popen, PIPE
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem

from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction

logger = logging.getLogger(__name__)
ext_icon = 'images/icon.png'
database_filepath = os.path.join(os.getenv("HOME"), '.locate-ulauncher-database')

class LocateExtension(Extension):

    def __init__(self):
        super(LocateExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        pattern = str(event.get_argument())
        keyword = event.get_keyword()
        
        update_keyword = extension.preferences['update_keyword']
        locate_file_keyword = extension.preferences['locate_file_keyword']
        locate_dir_keyword = extension.preferences['locate_dir_keyword']

        locate_flags = extension.preferences['locate_flags']
        open_script = extension.preferences['open_script']
        terminal_emulator = extension.preferences['terminal_emulator']
        permissive_pattern = extension.preferences['permissive_pattern']

        if permissive_pattern == 'yes':
            pattern = '*' + pattern.replace(' ', '*') + '*'

        if keyword == locate_file_keyword:
            # locate a file or directory in database
            return RenderResultListAction(list(self.generate_results(extension, pattern, locate_flags, open_script, terminal_emulator, False)))
        elif keyword == locate_dir_keyword:
            # locate a directory in database
            return RenderResultListAction(list(self.generate_results(extension, pattern, locate_flags, open_script, terminal_emulator, True)))
        elif keyword == update_keyword:
            # update files database
            cmd = ' '.join(['updatedb', '--require-visibility', 'no', '--output', database_filepath])
            logger.debug('Database update command: %s ' % cmd)
            show_notification('Information', 'Updating database...')
            return RunScriptAction(cmd)

    def generate_results(self, extension, pattern, locate_flags, open_script, terminal_emulator, dirs_only):
        for (f) in get_file_list(extension, pattern, locate_flags, dirs_only):
            file_path = '%s' % os.path.abspath(f)
            file_dir = '%s' % os.path.abspath(os.path.join(file_path, os.pardir))
            yield ExtensionSmallResultItem(
                                           icon=get_icon(f), 
                                           name=file_path, 
                                           on_enter=RunScriptAction(' '.join([open_script, file_path])),
                                           on_alt_enter=RunScriptAction(' '.join([terminal_emulator, '--working-directory', file_dir])))


def get_icon(f):
    file = Gio.File.new_for_path("/")
    folder_info = file.query_info('standard::icon', 0, Gio.Cancellable())
    folder_icon = folder_info.get_icon().get_names()[0]
    icon_theme = Gtk.IconTheme.get_default()
    icon_folder = icon_theme.lookup_icon(folder_icon, 128, 0)
    if icon_folder:
        folder_icon = icon_folder.get_filename()
    else:
        folder_icon = "images/folder.png"

    if os.path.isdir(f):
        icon = folder_icon
    else:
        type_, encoding = mimetypes.guess_type(f)

        if type_:
            file_icon = Gio.content_type_get_icon(type_)
            file_info = icon_theme.choose_icon(file_icon.get_names(), 128, 0)
            if file_info:
                icon = file_info.get_filename()
            else:
                icon = "images/file.png"
        else:
            icon = "images/file.png"

    return icon

def get_file_list(extension, pattern, flags, dirs_only):
    """
    Returns a list filenames.
    """
    cmd = ['locate', '--database', database_filepath]

    if not os.path.isfile(database_filepath):
        show_notification('Error', 'Must update database first')

    for flag in flags.split(' '):
        cmd.append(flag)

    cmd.append(pattern)
    logger.debug('Locating files with pattern: %s ' % (','.join(cmd)))
    process = Popen(cmd, stdout=PIPE)
    out = process.communicate()[0].decode('utf8')
    files = out.split('\n')
    if dirs_only: 
        return filter(lambda f: os.path.isdir(f), files)
    else:
        return files

def show_notification(title, text=None, icon=ext_icon):
    logger.debug('Show notification: %s' % text)
    icon_full_path = os.path.join(os.path.dirname(__file__), icon)
    Notify.init("LocateExtension")
    Notify.Notification.new(title, text, icon_full_path).show()


if __name__ == '__main__':
    LocateExtension().run()
