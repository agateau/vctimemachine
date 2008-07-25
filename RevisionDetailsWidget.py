from PyQt4.QtGui import *

from Ui_RevisionDetailsWidget import *

class RevisionDetailsWidget(QWidget, Ui_RevisionDetailsWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.setupUi(self)
