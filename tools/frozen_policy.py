# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Limit the offline executable to its required Qt components."""
import re
from pathlib import PurePosixPath

# QtSvg remains required by the bundled theme icons.
UNUSED_QT_MODULES = (
    'QtNetwork', 'QtWebSockets', 'QtWebChannel', 'QtWebEngineCore', 'QtWebEngineWidgets',
    'QtWebEngineQuick', 'QtQml', 'QtQuick', 'QtQuickWidgets', 'QtMultimedia',
    'QtMultimediaWidgets', 'QtBluetooth', 'QtNfc', 'QtPositioning', 'QtLocation',
    'QtRemoteObjects', 'QtSensors', 'QtSerialPort', 'QtSql', 'QtXml', 'QtPdf',
    'QtPdfWidgets', 'QtPrintSupport', 'QtDesigner', 'QtHelp', 'QtTest',
    'QtTextToSpeech', 'Qt5Compat', 'QtCore5Compat',
)
EXCLUDES = ('tkinter', 'PyQt5', 'PySide2', 'PySide6') + tuple('PyQt6.' + n for n in UNUSED_QT_MODULES)
_MODULE = re.compile(r'^(?:lib)?Qt6?(' + '|'.join(re.escape(n[2:]) for n in UNUSED_QT_MODULES)
                     + r')[A-Za-z0-9_]*(?:\.(?:dll|so|pyd)|\.abi|\.cpython|$)', re.IGNORECASE)


def forbidden_entry(name):
    path = name.replace('\\', '/')
    leaf = PurePosixPath(path).name
    return (bool(_MODULE.match(leaf)) or path in EXCLUDES
            or any(path.startswith(n + '.') for n in EXCLUDES)
            or leaf.lower() in ('qvnc.dll', 'libqvnc.so', 'libqvnc.dylib'))


def check_archive(path, reader_factory=None):
    if reader_factory is None:
        from PyInstaller.archive.readers import CArchiveReader
        reader_factory = CArchiveReader
    archive = reader_factory(str(path))
    names = list(archive.toc)
    for name, entry in archive.toc.items():
        if entry[-1] == 'z':
            names.extend(archive.open_embedded_archive(name).toc)
    unwanted = sorted(n for n in names if forbidden_entry(n))
    if unwanted:
        raise RuntimeError('Unexpected offline executable components: ' + ', '.join(unwanted))
    for module in ('QtCore', 'QtGui', 'QtWidgets'):
        if not any(n.replace('\\', '/').startswith('PyQt6/' + module + '.') for n in names):
            raise RuntimeError('Missing required Qt extension: ' + module)
    return {'status': 'passed', 'archive_entries': len(names)}


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable')
    print(json.dumps(check_archive(parser.parse_args().executable)))
