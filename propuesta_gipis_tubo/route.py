#!/usr/bin/env python3
"""Ruteo automático en una cara (B.Cu) con Freerouting.

pcbnew → DSN → se borra la capa F.Cu y las vías → Freerouting → SES → pcbnew.
Uso: python3 route.py [pasadas]   (deja nodo_a_ruteada.kicad_pcb)
"""
import re
import subprocess
import sys

import pcbnew

JAR = '/home/pablo/.local/share/freerouting/freerouting-2.4.1.jar'
PASSES = sys.argv[1] if len(sys.argv) > 1 else '40'

b = pcbnew.LoadBoard('nodo_a.kicad_pcb')
pcbnew.ExportSpecctraDSN(b, 'out/nodo_a.dsn')

dsn = open('out/nodo_a.dsn').read()
MODE = sys.argv[2] if len(sys.argv) > 2 else 'puentes'
if MODE == '1cara':
    # sin capa F.Cu ni vías: todo abajo
    dsn = re.sub(r'\(layer F\.Cu\s*\(type signal\)\s*\(property\s*\(index 0\)\s*\)\s*\)', '', dsn, count=1)
    dsn = re.sub(r'\(via "[^"]+"\)', '', dsn)
    dsn = re.sub(r'\(shape \((?:circle|rect|path|polygon) F\.Cu[^()]*\)\)', '', dsn)
else:
    # F.Cu = capa de puentes de alambre: solo se conecta a vías (agujeros propios),
    # nunca a pads de componentes (los zócalos no se sueldan del lado de arriba)
    def strip(m):
        blk = m.group(0)
        if blk.startswith('(padstack "Via') or blk.startswith('(padstack Via'):
            return blk
        return re.sub(r'\(shape \((?:circle|rect|path|polygon) F\.Cu[^()]*\)\)', '', blk)
    dsn = re.sub(r'\(padstack [^\n]*\n(?:\s+\(shape[^\n]*\n)+\s+\(attach[^\n]*\n\s+\)', strip, dsn)

    # ...pero el cobre del pad SÍ existe arriba (placa doble faz): keepout en
    # F.Cu sobre cada pin para que ningún puente pase por encima de un pad.
    def size(ps):
        nums = [int(float(n)) for n in re.findall(r'(\d+(?:\.\d+)?)(?=x|_um)', ps)]
        return max(nums) if nums else 2000

    def keepouts(m):
        img = m.group(0)
        ko = ''.join(f'      (keepout "" (circle F.Cu {size(ps)} {x} {y}))\n'
                     for ps, x, y in re.findall(
                         r'\(pin (\S+) (?:\(rotate [^)]*\) )?\S+ (-?[\d.]+) (-?[\d.]+)\)', img))
        return img[:img.rindex(')')] + ko + '    )'
    dsn = re.sub(r'\(image [^\n]*\n(?:\s+\((?:outline|pin|keepout)[^\n]*\n)*\s+\)', keepouts, dsn)
# El borde de 1 mm (fresa de contorno) no viaja en el DSN: se achica el
# contorno 0.4 mm (más los 0.6 de aislación que Freerouting ya respeta).
def inset(m):
    nums = [float(v) for v in m.group(2).split()]
    xs, ys = nums[0::2], nums[1::2]
    x0, x1, y0, y1 = min(xs) + 400, max(xs) - 400, min(ys) + 400, max(ys) - 400
    pts = [(x1, y0), (x0, y0), (x0, y1), (x1, y1), (x1, y0)]
    return m.group(1) + '  '.join(f'{x:.0f} {y:.0f}' for x, y in pts) + ')'
dsn = re.sub(r'(\(boundary\s*\(path pcb \d+\s+)([-\d.\s]+)\)', inset, dsn, count=1)
open('out/nodo_a_1cara.dsn', 'w').write(dsn)

r = subprocess.run(['java', '-jar', JAR, '-de', 'out/nodo_a_1cara.dsn', '-do', 'out/nodo_a.ses',
                    '-mp', PASSES, '--gui.enabled=false'],
                   capture_output=True, text=True, timeout=1800)
log = r.stdout + r.stderr
open('out/freerouting.log', 'w').write(log)
print('\n'.join(l for l in log.splitlines() if re.search(r'unrouted|pass|error|Error|completed|SES', l))[-2500:])

b = pcbnew.LoadBoard('nodo_a.kicad_pcb')
ok = pcbnew.ImportSpecctraSES(b, 'out/nodo_a.ses')
print('SES importado:', ok)
pcbnew.SaveBoard('nodo_a_ruteada.kicad_pcb', b)

# Conteo de puentes: tramos conexos de F.Cu
fc = [t for t in b.GetTracks() if t.GetLayer() == pcbnew.F_Cu and t.GetClass() == 'PCB_TRACK']
vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
pts = {}
def key(p): return (round(p.x / 1e4), round(p.y / 1e4))
par = {}
def find(a):
    while par.setdefault(a, a) != a:
        a = par[a]
    return a
for t in fc:
    par[find(key(t.GetStart()))] = find(key(t.GetEnd()))
grupos = {find(k) for k in par}
print(f'vías: {len(vias)}  segmentos arriba: {len(fc)}  PUENTES: {len(grupos)}')
