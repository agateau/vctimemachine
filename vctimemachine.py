#!/usr/bin/env python
import cgi
import os
import sys
import subprocess
import xml.etree.ElementTree as ET

from PyQt4.QtCore import *
from PyQt4.QtGui import *


def getUrlRevisions(url):
    cmd = ["svn", "log", "-q", "--limit", "10", url]
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout
    revs = []
    for line in pipe.readlines():
        if line[0] == 'r':
            tokens = line[1:].strip().split('|')
            rev = int(tokens[0])
            revs.append(rev)
    return revs


def getLatestRevisionForUrl(url):
    cmd = ["svn", "info", "--xml", url]
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout
    tree = ET.parse(pipe)
    commitElement = tree.getroot().find("entry/commit")
    assert commitElement
    return int(commitElement.attrib["revision"])


def getUrlAtRevision(url, revision):
    cmd = ["svn", "cat", "-r", str(revision), url]
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout
    return unicode(pipe.read(), "utf-8")


def getRevisionLog(url, revision):
    cmd = ["svn", "log", "-v", "-r", str(revision), url]
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout
    return unicode(pipe.read(), "utf-8")


def formatSource(url, revision):
    def fixSpaces(txt):
        return txt.replace(" ", "&nbsp;")

    lines = getUrlAtRevision(url, revision).split("\n")

    cmd = ["svn", "annotate", "--xml", "-r", str(revision), url]
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout
    tree = ET.parse(pipe)
    sourceLines = []

    commits = tree.getroot().findall("target/entry/commit")
    for lineNumber, (code, commit) in enumerate(zip(lines, commits)):

        rev = commit.attrib["revision"]
        author = commit.findtext("author")
        date = commit.findtext("date")

        lineNumberHtml = str(lineNumber + 1).rjust(5)
        lineNumberHtml = fixSpaces(lineNumberHtml)

        revHtml = fixSpaces(rev.rjust(8))
        if int(rev) == revision:
            revClass = "current"
        else:
            revClass = ""
        revHtml = "<a class='%s' href='r%s' title='%s'>%s</a>" % (revClass, rev, date, revHtml)

        authorHtml = cgi.escape(author.rjust(10))
        authorHtml = fixSpaces(authorHtml)

        codeHtml = cgi.escape(code).replace("\t", " "*4)
        codeHtml = fixSpaces(codeHtml)

        line = "%s, %s, %s, %s<br>" % (lineNumberHtml, revHtml, authorHtml, codeHtml)
        sourceLines.append(line)
    html = """<html>
        <head>
        <style>
        a.current {
            color: red;
        }
        </style>
        </head>
        <body>
        %s
        </body>
        </html>"""
    sourceHtml = "\n".join(sourceLines)
    return html % sourceHtml


class Window(QMainWindow):
    def __init__(self, url):
        QWidget.__init__(self)
        self.url = url

        fixedFont = QFont("Fixed")
        fixedFont.setStyleHint(QFont.TypeWriter)

        # Source browser
        self.sourceBrowser = QTextBrowser()
        self.sourceBrowser.setFont(fixedFont)
        self.sourceBrowser.setOpenLinks(False)

        self.setCentralWidget(self.sourceBrowser)

        # Revision details
        self.detailsLabel = QLabel()
        self.goToPreviousButton = QPushButton()
        self.goToCurrentButton = QPushButton()
        self.goToNextButton = QPushButton()
        self.revisionDetailsBrowser = QTextBrowser()
        self.revisionDetailsBrowser.setFont(fixedFont)

        self.revisionDetailsWidget = QWidget()
        layout = QGridLayout(self.revisionDetailsWidget)
        layout.setMargin(0)
        layout.addWidget(self.detailsLabel, 0, 0)
        layout.addWidget(self.goToPreviousButton, 0, 1)
        layout.addWidget(self.goToCurrentButton, 0, 2)
        layout.addWidget(self.goToNextButton, 0, 3)
        layout.addWidget(self.revisionDetailsBrowser, 1, 0, 1, 4)

        dockWidget = QDockWidget("Details")
        dockWidget.setWidget(self.revisionDetailsWidget)
        self.revisionDetailsWidget.hide()
        self.addDockWidget(Qt.BottomDockWidgetArea, dockWidget)

        # Connections
        QObject.connect(self.sourceBrowser, SIGNAL("anchorClicked(const QUrl&)"), self.slotSourceAnchorClicked)
        QObject.connect(self.goToPreviousButton, SIGNAL("clicked()"), self.goToPrevious)
        QObject.connect(self.goToCurrentButton, SIGNAL("clicked()"), self.goToCurrent)
        QObject.connect(self.goToNextButton, SIGNAL("clicked()"), self.goToNext)

        revision = getLatestRevisionForUrl(url)
        self.goToRevision(revision)

    def goToRevision(self, revision):
        source = formatSource(self.url, revision)
        self.sourceBrowser.setHtml(source)
        self.currentRevision = revision
        self.setWindowTitle("%s r%d" % (self.url,self.currentRevision))

    def goToNext(self):
        revision = self.currentRevision + 1
        self.goToRevision(revision)

    def goToCurrent(self):
        self.goToRevision(self.currentRevision)

    def goToPrevious(self):
        revision = self.currentRevision - 1
        self.goToRevision(revision)

    def sizeHint(self):
        return QSize(800, 600)

    def slotSourceAnchorClicked(self, link):
        link = unicode(link.toString())
        if link[0] == "r":
            revision = int(link[1:])
            self.showRevisionDetails(revision)

    def showRevisionDetails(self, revision):
        self.revisionDetailsWidget.show()

        self.currentRevision = revision
        details = getRevisionLog(self.url, self.currentRevision)
        self.revisionDetailsBrowser.setText(details)

        self.detailsLabel.setText("Showing details for r%d" % self.currentRevision)

        self.goToPreviousButton.setText("Go to r%d" % (self.currentRevision - 1))

        self.goToCurrentButton.setText("Go to r%d" % self.currentRevision)

        self.goToNextButton.setText("Go to r%d" % (self.currentRevision + 1))


def main():
    app = QApplication(sys.argv)
    url = sys.argv[1]
    url = os.path.abspath(url)
    window = Window(url)

    window.show()
    app.exec_()


if __name__=="__main__":
    main()
