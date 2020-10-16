import logging

from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import pymel.core as pmc
from pymel.core.system import Path

log = logging.getLogger(__name__)


def maya_main_window():
    """Return the maya main window widget."""
    if __name__ == '__main__':
        main_window = omui.MQtUtil.mainWindow()
        return wrapInstance(long(main_window), QtWidgets.QWidget)


class SmartSaveUI(QtWidgets.QDialog):
    """Smart Class UI Class"""

    def __init__(self):
        super(SmartSaveUI, self).__init__(parent=maya_main_window())
        self.setWindowTitle("Smart Save")
        self.setMinimumWidth(500)
        self.setMaxiumumHeight(200)
        self.setWindowFlags(self.windowFlags() ^
                            QtCore.Qt.WindowContextHelpButtonHint)
        self.create_ui()

    def create_ui(self):
        self.title_lbl = QtWidgets.Qlabel("Smart Save")
        self.title_lbl.setStyleSheet("font: bold 28px")
        self.folder_le = QtWidgets.QLineEdit("D:\\")
        self.folder_browse_btn = QtWidgets.QPushButton("...")
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.folder_le)
        layout.addWidget(self.folder_browse_btn)
        self.main_lay = QtWidgets.QVBoxLayout()
        self.main_lay.addWidget(self.title_lbl)
        self.main_lay.addLayout()
        self.setLayout(self.main_lay)



class SceneFile(object):
    """An abstract representation of a Scene file."""
    def __init__(self, path=None):
        self.folder_path = Path()
        self.descriptor = 'main'
        self.task = None
        self.ver = 1
        self.ext = '.ma'
        scene = pmc.system.sceneName()
        if not path and scene:
            path = scene
        if not path and not scene:
            log.warning("Unable to initialise SceneFile object from"
                        "a new scene. Please specify a path.")
            return
        self._init_from_path(path)

    @property
    def filename(self):
        pattern = "{descriptor}_{task}_v{ver:03d}{ext}"
        return pattern.format(descriptor=self.descriptor,
                              task=self.task,
                              ver=self.ver,
                              ext=self.ext)

    @property
    def path(self):
        return self.folder_path / self.filename

    def _init_from_path(self, path):
        path = Path(path)
        self.folder_path = path.parent
        self.ext = path.ext
        self.descriptor, self.task, ver = path.stripext().split("_")
        self.ver = int(ver.split("v")[-1])

    def save(self):
        """Saves the scene file.

        Returns:
            Path: The path to the scene file if successful.
        """
        try:
            return pmc.system.saveAs(self.path)
        except RuntimeError as err:
            log.warning("Missing directories in path. Creating"
                        "directories...")
            self.folder_path.makedirs_p()
            return pmc.system.saveAs(self.path)

    def next_avail_ver(self):
        """Returns the next available version number in the folder."""
        pattern = "{descriptor}_{task}_v{ext}".format(
            descriptor=self.descriptor, task=self.task, ext=self.ext)
        matching_scenefiles = []
        for file_ in self.folder_path.files():
            if file_.name.fnmatch(pattern):
                matching_scenefiles.append(file_)
        if not matching_scenefiles:
            return 1
        matching_scenefiles.sort(reverse=True)
        latest_scenefile = matching_scenefiles[0]
        latest_scenefile = latest_scenefile.name.stripext()
        latest_ver_num = int(latest_scenefile.split("v")[-1])
        return latest_ver_num + 1


    def increment_save(self):
        """Increments the version and saves the scene file.

        If the existing version of a file already exists, it should
        increment from the largest version number available in the
        folder.

        Returns:
            Path: The path the scene file if successful.
        """
        self.ver = self.next_avail_ver()
        self.save()