# -*- coding: utf-8 -*-
# Copyright (c) 2026 Geoazimut SàRL (https://geoazimut.com). Tous droits réservés.
"""Boîte d'ajout / modification d'un périphérique, et utilitaires d'affichage associés.
Aucune règle métier ici : seules les plages de saisie de 03_Modele_de_donnees.md sont appliquées,
la validation reste faite par elpro_engine.valider()."""
import os, re

from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QStandardItemModel, QStandardItem, QRegularExpressionValidator, QPixmap
from PySide6.QtWidgets import (QDialog, QFormLayout, QVBoxLayout, QComboBox, QLineEdit, QDoubleSpinBox,
                               QSpinBox, QDialogButtonBox, QWidget, QLabel, QHBoxLayout, QPushButton,
                               QPlainTextEdit, QMessageBox)

import elpro_engine as M
from version import APP_VERSION, APP_COPYRIGHT, APP_WEBSITE

# Libellés à afficher, dans l'ordre de la table de 03_Modele_de_donnees.md
LIBELLES = {
    'CABLE': 'Câble (détection)',
    'LIDAR3': 'Lidar 3 sorties',
    'LIDAR6': 'Lidar 6 sorties',
    'ALARME_BT': 'Alarme bouton/BT',
    'ENTREE': 'Entrée générique',
    'RADAR': 'Radar (4-20 mA)',
    'FEU': 'Feu',
    'SIRENE': 'Sirène',
    'FLASH': 'Flash',
    'SIRENE_FLASH': 'Sirène + flash (1 sortie)',
    'CAMERA': 'Caméra',
    'SPOT': 'Spot',
    'CAMERA_SPOT': 'Caméra + spot (1 commande)',
    'SORTIE': 'Sortie générique',
}
ENTREES_SIMPLES = ('CABLE', 'ALARME_BT', 'ENTREE')
LIDARS = {'LIDAR3': 3, 'LIDAR6': 6}
SORTIES_SIMPLES = ('SIRENE', 'FLASH', 'SIRENE_FLASH', 'CAMERA', 'SPOT', 'SORTIE')
# Sorties d'un feu : (clé JSON, libellé de la liste, abréviation de la colonne Câblage)
SORTIES_FEU = (('do_rouge', 'Sortie rouge', 'R'), ('do_orange_cli', 'Sortie orange clignotant', 'OC'),
               ('do_orange_fixe', 'Sortie orange fixe', 'OF'), ('do_vert', 'Sortie verte', 'V'))
NOM_FIXE = {'LIDAR3': 'LIDAR', 'LIDAR6': 'LIDAR', 'ALARME_BT': 'BT_ALARME', 'SIRENE': 'SIRENE', 'FLASH': 'FLASH',
            'SIRENE_FLASH': 'SIRENE_FLASH', 'CAMERA': 'CAM', 'SPOT': 'SPOT', 'CAMERA_SPOT': 'CAM'}


def nombre_fr(x):
    """12.0 -> '12' ; 12.5 -> '12,5'."""
    return f'{x:g}'.replace('.', ',') if isinstance(x, (int, float)) else str(x)


def _plage(prefixe, valeurs):
    v = [x for x in valeurs if x is not None]
    if len(v) > 1 and v == list(range(v[0], v[0] + len(v))):
        return f'{prefixe}{v[0]}-{prefixe}{v[-1]}'
    return ', '.join(f'{prefixe}{x}' for x in v)


def texte_cablage(p):
    """Résumé du câblage d'un périphérique pour le tableau de la page 1."""
    t = p.get('type')
    if t in ENTREES_SIMPLES or t in LIDARS:
        return _plage('DI', p.get('di', []))
    if t == 'RADAR':
        return f"AI{p.get('ai')} — seuil {nombre_fr(p.get('seuil_haut_ma'))} mA"
    if t == 'FEU':
        return ' · '.join(f'{abr} DO{p[cle]}' for cle, _l, abr in SORTIES_FEU if p.get(cle) is not None)
    if t == 'CAMERA_SPOT':
        return f"DO{p.get('do_camera')}/DO{p.get('do_spot')}"
    if t in SORTIES_SIMPLES:
        return f"DO{p.get('do')}"
    return ''


def occupations(radio, sauf=None):
    """Entrées/sorties déjà prises dans la radio : ({di: nom}, {do: nom}, {ai: nom}).
    `sauf` = index du périphérique à ignorer (celui qu'on modifie), ou 'MAINV'."""
    di, do, ai = {}, {}, {}
    mv = radio.get('mainv') or {}
    if mv.get('actif') and sauf != 'MAINV':
        di[mv.get('di', 8)] = 'MAINV'
    for i, p in enumerate(radio.get('peripheriques', [])):
        if i == sauf:
            continue
        nom = p.get('nom', '')
        for d in p.get('di', []) if p.get('type') in M.TYPES_ENTREE else []:
            di.setdefault(d, nom)
        for d in M.sorties_du_periph(p):
            if d is not None:
                do.setdefault(d, nom)
        if p.get('type') == 'RADAR' and p.get('ai') is not None:
            ai.setdefault(p['ai'], nom)
    return di, do, ai


def remplir_combo(cb, prefixe, valeurs, occupes, aucune=False):
    """Remplit une liste DI/DO/AI ; les entrées occupées sont grisées avec le nom de l'occupant."""
    m = QStandardItemModel(cb)
    if aucune:
        it = QStandardItem('aucune'); it.setData(None, Qt.UserRole); m.appendRow(it)
    for v in valeurs:
        it = QStandardItem(f'{prefixe}{v}' + (f' ({occupes[v]})' if v in occupes else ''))
        it.setData(v, Qt.UserRole)
        if v in occupes:
            it.setEnabled(False)
        m.appendRow(it)
    cb.setModel(m)


def choisir(cb, valeur):
    i = cb.findData(valeur, Qt.UserRole)
    if i >= 0:
        cb.setCurrentIndex(i)


def premier_libre(valeurs, occupes, aussi=()):
    for v in valeurs:
        if v not in occupes and v not in aussi:
            return v
    return valeurs[0]


class DialoguePeripherique(QDialog):
    def __init__(self, parent, projet, radio, index=None):
        super().__init__(parent)
        self.projet, self.radio, self.index = projet, radio, index
        self.setWindowTitle('Modifier le périphérique' if index is not None else 'Ajouter un périphérique')
        self.setMinimumWidth(420)
        self.occ_di, self.occ_do, self.occ_ai = occupations(radio, sauf=index)
        existant = radio['peripheriques'][index] if index is not None else None
        self.nom_saisi = existant is not None          # le nom proposé n'est plus remplacé une fois saisi

        self.cb_type = QComboBox()
        for t, lib in LIBELLES.items():          # tous les types pour toutes les radios, base comprise
            self.cb_type.addItem(lib, t)
        self.ed_nom = QLineEdit()
        self.ed_nom.setMaxLength(16)
        self.ed_nom.setValidator(QRegularExpressionValidator(QRegularExpression(r'[A-Za-z0-9_]{0,16}'), self))
        self.ed_nom.textEdited.connect(self._nom_edite)

        haut = QFormLayout()
        haut.addRow('Type', self.cb_type)
        haut.addRow('Nom', self.ed_nom)
        self.zone = QWidget()
        self.form = QFormLayout(self.zone)
        self.form.setContentsMargins(0, 0, 0, 0)
        boutons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        boutons.button(QDialogButtonBox.Ok).setText('OK')
        boutons.button(QDialogButtonBox.Cancel).setText('Annuler')
        boutons.accepted.connect(self.accept)
        boutons.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(haut)
        titre = QLabel('<b>Câblage</b>')
        lay.addWidget(titre)
        lay.addWidget(self.zone)
        lay.addStretch(1)
        lay.addWidget(boutons)

        self.champs = {}
        if existant:
            choisir(self.cb_type, existant.get('type'))
            self._creer_champs(existant.get('type'), existant)
            self.ed_nom.setText(existant.get('nom', ''))
        else:
            self._creer_champs(self.cb_type.currentData(), None)
        self.cb_type.currentIndexChanged.connect(lambda _: self._creer_champs(self.cb_type.currentData(), None))

    # ---------------------------------------------------------------- nom proposé
    def _nom_edite(self, _):
        self.nom_saisi = True

    def _noms_radio(self):
        return {p.get('nom') for i, p in enumerate(self.radio.get('peripheriques', [])) if i != self.index}

    def _unique(self, base, numerote=False, depart=1):
        noms = self._noms_radio()
        if numerote:
            n = depart
            while f'{base}{n}' in noms:
                n += 1
            return f'{base}{n}'
        if base not in noms:
            return base
        n = 2
        while f'{base}{n}' in noms:
            n += 1
        return f'{base}{n}'

    def _nom_propose(self, t):
        if t == 'CABLE':
            return self._unique('CABLE', True)
        if t == 'FEU':
            feux = {p.get('nom') for r in self.projet['radios'] for p in r.get('peripheriques', []) if p.get('type') == 'FEU'}
            n = sum(1 for r in self.projet['radios'] for p in r.get('peripheriques', []) if p.get('type') == 'FEU') + 1
            while f'F{n}' in feux or f'F{n}' in self._noms_radio():
                n += 1
            return f'F{n}'
        if t == 'RADAR':
            nb = sum(1 for p in self.radio.get('peripheriques', []) if p.get('type') == 'RADAR')
            return self._unique('RADAR', True, nb + 1)
        if t == 'ENTREE':
            return self._unique(f"DI{self.champs['di0'].currentData()}")
        if t == 'SORTIE':
            return self._unique(f"DO{self.champs['do'].currentData()}")
        return self._unique(NOM_FIXE.get(t, t))

    def _proposer_nom(self):
        if not self.nom_saisi:
            self.ed_nom.setText(self._nom_propose(self.type))

    # ---------------------------------------------------------------- champs de câblage
    def _combo(self, libelle, cle, prefixe, valeurs, occupes, aucune=False):
        cb = QComboBox()
        remplir_combo(cb, prefixe, valeurs, occupes, aucune)
        self.form.addRow(libelle, cb)
        self.champs[cle] = cb
        return cb

    def _spin(self, libelle, cle, mini, maxi, pas, defaut, decimales=1, suffixe=''):
        if decimales:
            sp = QDoubleSpinBox(); sp.setDecimals(decimales); sp.setSingleStep(pas)
        else:
            sp = QSpinBox()
        sp.setRange(mini, maxi)
        sp.setValue(defaut)
        sp.setSuffix(suffixe)
        self.form.addRow(libelle, sp)
        self.champs[cle] = sp
        return sp

    def _creer_champs(self, t, p):
        self.type = t
        while self.form.rowCount():
            self.form.removeRow(0)
        self.champs = {}
        DI, DO, AI = list(range(1, 9)), list(range(1, 9)), list(range(1, 5))
        if t in ENTREES_SIMPLES:
            cb = self._combo('Entrée', 'di0', 'DI', DI, self.occ_di)
            choisir(cb, p['di'][0] if p and p.get('di') else premier_libre(DI, self.occ_di))
            if t == 'ENTREE':
                cb.currentIndexChanged.connect(lambda _: self._proposer_nom())
        elif t in LIDARS:
            n = LIDARS[t]
            debuts = list(range(1, 9 - n + 1))
            cb0 = self._combo('Première entrée', 'premiere', 'DI', debuts, self.occ_di)
            for k in range(n):
                self._combo(f'Entrée {k + 1}', f'di{k}', 'DI', DI, self.occ_di)
            if p and len(p.get('di', [])) == n:
                choisir(cb0, p['di'][0])
                for k, d in enumerate(p['di']):
                    choisir(self.champs[f'di{k}'], d)
            else:
                libre = next((d for d in debuts if all(x not in self.occ_di for x in range(d, d + n))),
                             premier_libre(debuts, self.occ_di))
                choisir(cb0, libre)
                self._suite_lidar(n)
            cb0.currentIndexChanged.connect(lambda _: self._suite_lidar(n))
        elif t == 'FEU':
            cbs = {cle: self._combo(lib, cle, 'DO', DO, self.occ_do, aucune=True) for cle, lib, _a in SORTIES_FEU}
            if p:
                for cle, cb in cbs.items():
                    choisir(cb, p.get(cle))
            else:           # proposé : rouge et orange clignotant sur les premières sorties libres, le reste « aucune »
                a = premier_libre(DO, self.occ_do)
                choisir(cbs['do_rouge'], a)
                choisir(cbs['do_orange_cli'], premier_libre(DO, self.occ_do, (a,)))
                choisir(cbs['do_orange_fixe'], None); choisir(cbs['do_vert'], None)
        elif t in SORTIES_SIMPLES:
            cb = self._combo('Sortie', 'do', 'DO', DO, self.occ_do)
            choisir(cb, p.get('do') if p else premier_libre(DO, self.occ_do))
            if t == 'SORTIE':
                cb.currentIndexChanged.connect(lambda _: self._proposer_nom())
        elif t == 'CAMERA_SPOT':
            c = self._combo('Sortie caméra', 'do_camera', 'DO', DO, self.occ_do)
            s = self._combo('Sortie spot', 'do_spot', 'DO', DO, self.occ_do)
            if p:
                choisir(c, p.get('do_camera')); choisir(s, p.get('do_spot'))
            else:
                a = premier_libre(DO, self.occ_do); choisir(c, a); choisir(s, premier_libre(DO, self.occ_do, (a,)))
        elif t == 'RADAR':
            cb = self._combo('Entrée analogique', 'ai', 'AI', AI, self.occ_ai)
            choisir(cb, p.get('ai') if p else premier_libre(AI, self.occ_ai))
            self._spin('Seuil haut', 'seuil_haut_ma', 4.1, 19.9, 0.1, p.get('seuil_haut_ma', 12.0) if p else 12.0, suffixe=' mA')
            self._spin('Hystérésis', 'hysteresis_ma', 0.1, 15.8, 0.1, p.get('hysteresis_ma', 0.8) if p else 0.8, suffixe=' mA')
            self._spin('Variation déclenchant un envoi', 'variation_ma', 0.1, 8.0, 0.1,
                       p.get('variation_ma', 0.8) if p else 0.8, suffixe=' mA')
            self._spin('Intervalle minimal entre envois', 'tmin_s', 1, 3600, 1, p.get('tmin_s', 10) if p else 10,
                       decimales=0, suffixe=' s')
        if p is None:
            self._proposer_nom()

    def _suite_lidar(self, n):
        d = self.champs['premiere'].currentData()
        for k in range(n):
            choisir(self.champs[f'di{k}'], d + k)

    # ---------------------------------------------------------------- résultat
    def peripherique(self):
        """Élément à ranger dans radio['peripheriques'] (clés de 03_Modele_de_donnees.md)."""
        t, c = self.type, self.champs
        p = {'type': t, 'nom': self.ed_nom.text()}
        if t in ENTREES_SIMPLES:
            p['di'] = [c['di0'].currentData()]
        elif t in LIDARS:
            p['di'] = [c[f'di{k}'].currentData() for k in range(LIDARS[t])]
        elif t == 'FEU':
            p.update({cle: c[cle].currentData() for cle, _l, _a in SORTIES_FEU})
        elif t in SORTIES_SIMPLES:
            p['do'] = c['do'].currentData()
        elif t == 'CAMERA_SPOT':
            p.update(do_camera=c['do_camera'].currentData(), do_spot=c['do_spot'].currentData())
        elif t == 'RADAR':
            p.update(ai=c['ai'].currentData(), seuil_haut_ma=round(c['seuil_haut_ma'].value(), 1),
                     hysteresis_ma=round(c['hysteresis_ma'].value(), 1), variation_ma=round(c['variation_ma'].value(), 1),
                     tmin_s=int(c['tmin_s'].value()))
        return p


def site_affiche(url):
    """'https://geoazimut.com' -> 'geoazimut.com'."""
    return re.sub(r'^https?://', '', url).rstrip('/')


class AboutDialog(QDialog):
    """Fenêtre « À propos » : version, copyright, site web, licence et composants tiers.
    Toutes les mentions viennent de version.py ; LICENSE et THIRD_PARTY_NOTICES.md sont lus dans `base`."""
    FICHIERS = {'Licence': 'LICENSE', 'Composants tiers': 'THIRD_PARTY_NOTICES.md'}

    def __init__(self, parent, base):
        super().__init__(parent)
        self.base = base
        self.setWindowTitle("À propos d'ELPRO Config")
        self.setFixedSize(420, 360)
        lay = QVBoxLayout(self)
        lay.setSpacing(6)

        def ligne(texte, taille=None, gras=False, lien=False):
            l = QLabel(texte)
            l.setAlignment(Qt.AlignCenter)
            l.setWordWrap(True)
            if taille or gras:
                f = l.font()
                if taille:
                    f.setPointSize(taille)
                f.setBold(gras)
                l.setFont(f)
            if lien:
                l.setTextFormat(Qt.RichText)
                l.setOpenExternalLinks(True)
            lay.addWidget(l)
            return l

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        logo.setPixmap(QPixmap(os.path.join(base, 'resources', 'app_icon.png'))
                       .scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lay.addWidget(logo)
        ligne('ELPRO Config', taille=16, gras=True)
        ligne(f'Version {APP_VERSION}')
        ligne('Génération de configurations standardisées pour radios ELPRO 415U-2-C4.')
        ligne(APP_COPYRIGHT)
        self.lien = ligne(f'<a href="{APP_WEBSITE}">{site_affiche(APP_WEBSITE)}</a>', lien=True)
        ligne('Utilisation gratuite. Reproduction, modification et redistribution interdites sans '
              'autorisation écrite de Geoazimut SàRL.', taille=8)
        ligne('Outil indépendant, non affilié à ELPRO Technologies.', taille=8)
        lay.addStretch(1)

        boutons = QHBoxLayout()
        for texte in self.FICHIERS:
            b = QPushButton(texte)
            b.clicked.connect(lambda _=False, t=texte: self.afficher_fichier(t))
            boutons.addWidget(b)
        boutons.addStretch(1)
        fermer = QPushButton('Fermer')
        fermer.setDefault(True)
        fermer.clicked.connect(self.accept)
        boutons.addWidget(fermer)
        lay.addLayout(boutons)

    def texte_fichier(self, titre):
        """Contenu de LICENSE / THIRD_PARTY_NOTICES.md embarqué avec l'application ('' si absent)."""
        chemin = os.path.join(self.base, self.FICHIERS[titre])
        try:
            with open(chemin, encoding='utf-8') as f:
                return f.read()
        except OSError:
            return ''

    def afficher_fichier(self, titre):
        texte = self.texte_fichier(titre)
        if not texte:
            QMessageBox.warning(self, titre, f'Fichier introuvable : {self.FICHIERS[titre]}')
            return
        d = QDialog(self)
        d.setWindowTitle(titre)
        d.resize(640, 480)
        v = QVBoxLayout(d)
        zone = QPlainTextEdit(texte)
        zone.setReadOnly(True)
        v.addWidget(zone)
        b = QDialogButtonBox(QDialogButtonBox.Close)
        b.button(QDialogButtonBox.Close).setText('Fermer')
        b.rejected.connect(d.reject)
        v.addWidget(b)
        d.exec()
