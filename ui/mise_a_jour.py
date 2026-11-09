# -*- coding: utf-8 -*-
# Copyright (c) 2026 Geoazimut SàRL (https://geoazimut.com). Tous droits réservés.
"""Mise à jour automatique : recherche et téléchargement en arrière-plan, fenêtre « Mise à jour disponible ».
Le travail réseau est fait par engine/updater.py (U) ; ce module ne fait que l'interface."""
from PySide6.QtCore import Qt, QThread, Signal, QSettings, QEventLoop
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QPushButton,
                               QProgressDialog, QMessageBox)

import updater as U
from version import APP_VERSION

APP = 'ELPRO Config'
DEPOT, PREFIXE = U.DEPOT_CONFIG, U.PREFIXE_CONFIG
ANNULE = 'Téléchargement annulé.'      # message de U.telecharger quand l'utilisateur annule


class RechercheMaj(QThread):
    """Interroge GitHub dans un thread. fini(info ou None, message d'erreur ou '')."""
    fini = Signal(object, str)

    def run(self):
        try:
            info = U.chercher(DEPOT, U.version_pour_recherche(APP_VERSION), PREFIXE)
        except U.ErreurMiseAJour as x:
            self.fini.emit(None, str(x))
        except Exception as x:          # imprévu : traité comme une erreur réseau (rien n'est affiché en automatique)
            self.fini.emit(None, f'Erreur inattendue pendant la recherche de mise à jour : {x}')
        else:
            self.fini.emit(info, '')


class TelechargementMaj(QThread):
    """Télécharge et vérifie l'installateur. progression(reçus, total) ; fini(chemin ou '', erreur ou '')."""
    progression = Signal(int, int)
    fini = Signal(str, str)

    def __init__(self, info, parent=None):
        super().__init__(parent)
        self.info = info
        self._annule = False

    def annuler(self):
        self._annule = True

    def run(self):
        try:
            chemin = U.telecharger(self.info, progression=lambda r, t: self.progression.emit(r, t),
                                   annule=lambda: self._annule)
        except U.ErreurMiseAJour as x:
            self.fini.emit('', str(x))
        except Exception as x:
            self.fini.emit('', f'Erreur inattendue pendant le téléchargement : {x}')
        else:
            self.fini.emit(chemin, '')


def _mo(octets):
    return f'{octets / 1048576:.1f}'.replace('.', ',')


class FenetreMaj(QDialog):
    """« Mise à jour disponible » : notes de la version, Installer et redémarrer / Plus tard / Ignorer."""

    def __init__(self, parent, info):
        super().__init__(parent)
        self.info = info
        self.setWindowTitle('Mise à jour disponible')
        self.resize(560, 400)
        lay = QVBoxLayout(self)
        self.entete = QLabel(f"{APP} {info['version']} est disponible. Version installée : {APP_VERSION}.")
        self.entete.setWordWrap(True)
        lay.addWidget(self.entete)
        self.notes = QTextBrowser()
        self.notes.setOpenExternalLinks(True)
        self.notes.setMarkdown(info['notes'] or 'Pas de notes pour cette version.')
        self.notes.setMinimumHeight(220)
        lay.addWidget(self.notes)
        self.lien = QLabel(f'<a href="{info["page"]}">Voir la page de la version</a>')
        self.lien.setTextFormat(Qt.RichText)
        self.lien.setOpenExternalLinks(True)
        lay.addWidget(self.lien)

        boutons = QHBoxLayout()
        self.bt_installer = QPushButton('Installer et redémarrer')
        self.bt_installer.setDefault(True)
        self.bt_installer.clicked.connect(self.installer)
        self.bt_plus_tard = QPushButton('Plus tard')
        self.bt_plus_tard.clicked.connect(self.reject)
        self.bt_ignorer = QPushButton('Ignorer cette version')
        self.bt_ignorer.clicked.connect(self.ignorer)
        boutons.addWidget(self.bt_installer)
        boutons.addWidget(self.bt_plus_tard)
        boutons.addStretch(1)
        boutons.addWidget(self.bt_ignorer)
        lay.addLayout(boutons)

    def ignorer(self):
        QSettings().setValue('maj/version_ignoree', self.info['version'])
        self.reject()

    def installer(self):
        """Télécharge (annulable), puis confie l'installation à la fenêtre principale."""
        parent = self.parent()
        prog = QProgressDialog('Téléchargement de la mise à jour…', 'Annuler', 0, 0, self)
        prog.setWindowTitle('Mise à jour')
        prog.setWindowModality(Qt.WindowModal)
        prog.setMinimumDuration(0)
        prog.setAutoClose(False)
        prog.setAutoReset(False)
        t = TelechargementMaj(self.info, self)
        resultat = {}
        boucle = QEventLoop()

        def avancer(recus, total):
            if total:
                prog.setMaximum(total)
                prog.setValue(min(recus, total))
            prog.setLabelText(f'Téléchargement de la mise à jour…\n{_mo(recus)} Mo'
                              + (f' sur {_mo(total)} Mo' if total else ''))

        t.progression.connect(avancer)
        t.fini.connect(lambda chemin, erreur: (resultat.update(chemin=chemin, erreur=erreur), boucle.quit()))
        prog.canceled.connect(t.annuler)
        t.start()
        prog.show()
        boucle.exec()                   # jusqu'à la fin du thread (après une annulation aussi)
        t.wait()
        prog.close()
        if resultat['erreur']:
            if resultat['erreur'] != ANNULE:
                QMessageBox.warning(parent, 'Mise à jour', resultat['erreur'])
            return
        self.accept()
        parent.installer_maj(resultat['chemin'])
