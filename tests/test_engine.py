# -*- coding: utf-8 -*-
# Copyright (c) 2026 Geoazimut SàRL (https://geoazimut.com). Tous droits réservés.
"""Tests de recette du moteur. Lancer :  python -m unittest discover -s tests -v   (depuis le dossier livrable)
Tous les tests doivent passer avant toute livraison. Ne pas modifier les fichiers expected_*.json."""
import os, sys, json, re, unittest, tempfile, tarfile
from pathlib import Path
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, '..', 'engine'))
import elpro_engine as M

EX = os.path.join(ICI, '..', 'examples')


def charger(nom):
    return json.loads(Path(EX, f'{nom}.json').read_text(encoding='utf-8'))


def resume(plan):
    """Partie du plan figée dans expected_*.json (indépendante de la date)."""
    st = []
    for S in plan['stations']:
        st.append({k: S[k] for k in ('nom', 'uid', 'xx', 'role', 'ip', 'amont', 'puissance_dbm', 'ack')} | {
            'reads': S['reads'], 'scatters': [dict(m, paires=[list(p) for p in m['paires']]) for m in S['scatters']],
            'writes': S['writes'], 'failsafe': [list(x) for x in S['failsafe']],
            'iop': [list(l) for l in S['iop']] if S['iop'] else None,
            'noms_io': S['noms_io'], 'nb_tags': len(S['tags']), 'groupes': [list(g) for g in S['groupes']]})
    return json.loads(json.dumps({'T': plan['T'], 'registres': plan['registres'], 'stations': st}))


def simuler_iop(lignes, mem, cycles=1):
    """Interpréteur IO Plus (sous-ensemble utilisé). Sauts I=1 relatifs à la ligne du saut (validé sur radio)."""
    inv = {v: k for k, v in M.OP.items()}
    for _ in range(cycles):
        pc, acc = 0, 0
        while pc < len(lignes):
            op, I, N, _b, v, _c = lignes[pc]; o = inv[op]; arg = v if I else mem.get(v, 0); nxt = pc + 1
            if o == 'LOAD': acc = arg
            elif o == 'STOR': mem[v] = acc
            elif o == 'SET':
                if acc: mem[v] = 1
            elif o == 'RES':
                if acc: mem[v] = 0
            elif o == 'ADD': acc = (acc + arg) & 0xFFFF
            elif o == 'SUB': acc = (acc - arg) & 0xFFFF
            elif o == 'OR': acc = acc | arg
            elif o == 'XOR': acc = acc ^ arg
            elif o == 'GE': acc = int(acc >= arg)
            elif o == 'LE': acc = int(acc <= arg)
            elif o == 'LT': acc = int(acc < arg)
            elif o == 'NE': acc = int(acc != arg)
            elif o == 'JMP': nxt = pc + v if I else v - 1
            elif o == 'JMP_C':
                if (acc == 0) if N else (acc != 0): nxt = pc + v if I else v - 1
            else: raise AssertionError(o)
            pc = nxt
    return mem


class TestExemples(unittest.TestCase):
    def test_attendus(self):
        for nom in ('demo_site_A', 'demo_site_B'):
            with self.subTest(nom):
                plan = M.calculer_plan(charger(nom))
                att = json.loads(Path(EX, f'expected_{nom}.json').read_text(encoding='utf-8'))
                self.assertEqual(resume(plan), att)

    def test_fichiers(self):
        for nom in ('demo_site_A', 'demo_site_B'):
            with self.subTest(nom), tempfile.TemporaryDirectory() as d:
                plan, fichiers = M.generer_tout(charger(nom), d)
                cdb = Path(fichiers[0]).read_bytes()
                self.assertEqual(cdb[:2], b'\xff\xfe')                       # UTF-16 LE + BOM
                txt = cdb.decode('utf-16')
                self.assertIn('\r\n', txt)                                   # CRLF
                self.assertEqual(len(re.findall(r'<Unit Type="E2CI"', txt)), len(plan['stations']))
                for f in fichiers[1:]:
                    with tarfile.open(f) as tf:
                        self.assertEqual(sorted(tf.getnames()), ['Logic.conf', 'Logic.version'])
                        conf = tf.extractfile('Logic.conf').read().decode()
                        self.assertIn('<item name="Enabled"><val><![CDATA[0]]></val></item>', conf)   # livré désactivé
                        for c in re.findall(r'<val><!\[CDATA\[([^\]]*)\]\]></val></tr>', conf):
                            self.assertFalse(set(c) & set('<>&"\''), c)

    def test_iop_base_coherent(self):
        """Chaque bloc comflag additionne exactement les FailReg des lectures de la station ; seuil = nb de lectures."""
        for nom in ('demo_site_A', 'demo_site_B'):
            plan = M.calculer_plan(charger(nom)); B = plan['stations'][0]
            blocs, cur = [], []
            for l in B['iop']:
                cur.append(l)
                if l[0] == M.OP['STOR']: blocs.append(cur); cur = []
            for S in plan['stations'][1:]:
                bl = next(b for b in blocs if b[-1][4] == int(f"151{S['xx']}"))
                lus = sorted(m['fail'] for m in B['reads'] if m['dest'] == S['uid'])
                somme = sorted(l[4] for l in bl if l[0] in (M.OP['LOAD'], M.OP['ADD']))
                seuil = next(l[4] for l in bl if l[0] == M.OP['GE'])
                ou = [l[4] for l in bl if l[0] == M.OP['OR']]
                sg = [m['fail'] for m in B['scatters'] if m['dest'] == S['uid']]
                self.assertEqual(somme, lus); self.assertEqual(seuil, len(lus)); self.assertEqual(ou, sg)

    def test_polling(self):
        for nom in ('demo_site_A', 'demo_site_B'):
            plan = M.calculer_plan(charger(nom)); B = plan['stations'][0]
            per = [m for m in B['reads'] + B['scatters'] if m['periode']]
            offs = sorted(m['offset'] for m in per)
            self.assertEqual(offs, list(range(0, plan['T'], M.CRENEAU_S)))
            self.assertTrue(all(m['periode'] == plan['T'] for m in per))
            fs = [(a, a + c - 1) for a, c in B['failsafe']]
            for m in B['reads'] + B['scatters']:
                if m['fail']: self.assertTrue(any(a <= m['fail'] <= b for a, b in fs), m['nom'])

    def test_radar(self):
        """Comportement du bloc radar : envoi au démarrage, variation, tempo, seuils."""
        plan = M.calculer_plan(charger('demo_site_B'))
        S = next(X for X in plan['stations'] if X['radars']); R = S['radars'][0]
        mem, envois, prec = {}, [], 0
        seq = [20000] * 5 + [20500] * 50 + [22100] * 3 + [33000] * 60 + [31500] * 60 + [31000] * 60
        for t, v in enumerate(seq):
            mem[30000 + R['ai']] = v
            simuler_iop(S['iop'], mem)
            if mem.get(R['force'], 0) != prec:
                envois.append((t, v, mem[R['bloc'] + 2])); prec = mem[R['force']]
        self.assertEqual(envois, [(0, 20000, 0), (55, 22100, 0), (96, 33000, 1), (178, 31000, 0)])

    def test_validation(self):
        p = charger('demo_site_A')
        p['radios'][1]['peripheriques'].append({'type': 'CABLE', 'nom': 'X', 'di': [1]})
        self.assertTrue(any('DI1 déjà utilisée' in e for e in M.valider(p)))
        p = charger('demo_site_A'); p['radios'][2]['ip_octet'] = 101
        self.assertTrue(any('même adresse IP' in e for e in M.valider(p)))
        p = charger('demo_site_A'); p['radios'][0]['role'] = 'remote'
        self.assertTrue(M.valider(p))

    def test_nom_fichier(self):
        self.assertEqual(M.nom_fichier('Demo Site - A'), 'Demo_Site_A')
        self.assertEqual(M.nom_fichier('DEMO_B'), 'DEMO_B')
        self.assertEqual(M.nom_fichier(' -- '), 'projet')

    def test_cle(self):
        for _ in range(50):
            k = M.generer_cle()
            self.assertEqual(len(k), 24); self.assertFalse(set(k) & set('<>&"\' '))

    def test_import(self):
        with tempfile.TemporaryDirectory() as d:
            plan, f = M.generer_tout(charger('demo_site_A'), d)
            proj, av = M.importer_cdb(f[0])
            self.assertEqual([r['nom'] for r in proj['radios']], [S['nom'] for S in plan['stations']])
            self.assertEqual([r['role'] for r in proj['radios']], [S['role'] for S in plan['stations']])
            self.assertEqual(proj['systeme']['cle_chiffrement'], plan['systeme']['cle_chiffrement'])


if __name__ == '__main__':
    unittest.main()
