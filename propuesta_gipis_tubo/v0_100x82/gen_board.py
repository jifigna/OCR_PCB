#!/usr/bin/env python3
"""Nodo A (frame OCR Lu 0099) — generador del PCB, propuesta GIPIS v0.

Basado en la placa de Juan Figna (OCR_PCB_juan, commit eeee71c) con las
correcciones de la revisión 2026-10-09 (ver ../README.md). Método igual que
EOLOVITA (~/Projects/eolovita/hardware/nodo): una sola cara de cobre (B.Cu),
pistas >= 0.8 mm, aislación >= 0.6 mm, sin vías → LPKF ProtoMat del lab.

Coordenadas en mm, origen arriba a la izquierda, Y hacia abajo, vista superior.
Cada módulo lleva una caja 3D (VRML) con su altura estimada sobre la placa.
"""

import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
D3 = os.path.join(HERE, '3d')

# ---------------------------------------------------------------- parámetros
BOARD_W, BOARD_H = 100.0, 82.0
P = 2.54
SOCKET_H = 8.5          # tira hembra vertical 2.54
MOD_ON_SOCKET = 11.0    # base del módulo enchufado (hembra + plástico del macho)

# ---------------------------------------------------------------- nets
NETS = ["", "GND", "12V_IN", "12V", "+5V", "+5V_H", "VE",
        "SDA", "SCL", "SD_CS", "SD_MOSI", "SD_MISO", "SD_SCK",
        "GPS_TX", "GPS_RX", "OCR_TXD", "OCR_RXD", "TX_OCR", "RX_OCR",
        "RELE1", "RELE2", "NO1", "NO2", "VCC_RELE", "V+_OCR", "V+_SHUT",
        "C1+", "C1-", "C2+", "C2-", "V+", "V-", "ICM_INT", "F_OUT"]
N = {n: i for i, n in enumerate(NETS)}

# ---------------------------------------------------------------- piezas
# Una pieza: dict(ref, val, x, y, pads=[(num, dx, dy, net, kind)], boxes, holes)
#   kind: 'ov_v' oval alargado en Y (fila horizontal), 'ov_h' alargado en X
#         (fila vertical), 'rect_v'/'rect_h' pin 1, 'big' bornera/diodo
#   boxes: [(x0, y0, x1, y1, z0, z1, (r, g, b))] en coords locales
#   holes: [(dx, dy, diam)] agujeros sin cobre (tornillo del módulo)
PARTS = []


def row(n_pins, x0, y0, nets, horizontal=True, pitch=P, kind=None, first=1):
    """Fila de pads: horizontal → avanza en X; vertical → avanza en Y."""
    pads = []
    for i in range(n_pins):
        dx, dy = (x0 + pitch * i, y0) if horizontal else (x0, y0 + pitch * i)
        if kind:
            k = kind
        else:
            k = ('rect_' if i == 0 else 'ov_') + ('v' if horizontal else 'h')
        pads.append((str(first + i), dx, dy, nets[i], k))
    return pads


def part(ref, val, x, y, pads, boxes=(), holes=()):
    PARTS.append(dict(ref=ref, val=val, x=x, y=y, pads=pads,
                      boxes=list(boxes), holes=list(holes)))


BLACK, GREEN, BLUE, DARK = (.08, .08, .08), (.1, .6, .25), (.1, .25, .7), (.15, .15, .2)
SILVER, YELLOW, TAN = (.75, .75, .78), (.9, .75, .2), (.8, .65, .45)


def terminal(ref, val, x, y, nets):
    """Bornera 4UCON paso 3.5 vertical, pines hacia abajo (Y)."""
    n = len(nets)
    pads = row(n, 0, 0, [N[a] for a in nets], horizontal=False, pitch=3.5, kind='big')
    part(ref, val, x, y, pads,
         boxes=[(-3.5, -1.75, 3.5, 3.5 * n - 1.75, 0, 10, GREEN)])


def header_v(ref, val, x, y, nets, h=SOCKET_H):
    """Tira vertical (pines en Y) — hembra o macho, caja negra."""
    n = len(nets)
    pads = row(n, 0, 0, [N[a] if a else 0 for a in nets], horizontal=False)
    part(ref, val, x, y, pads,
         boxes=[(-1.27, -1.27, 1.27, P * n - 1.27, 0, h, BLACK)])


def header_h(ref, val, x, y, nets, h=SOCKET_H):
    n = len(nets)
    pads = row(n, 0, 0, [N[a] if a else 0 for a in nets], horizontal=True)
    part(ref, val, x, y, pads,
         boxes=[(-1.27, -1.27, P * n - 1.27, 1.27, 0, h, BLACK)])


# --- Bornes y jumpers (borde izquierdo) ------------------------------------
terminal('J1', 'OCR', 4.5, 7.5, ['TX_OCR', 'GND', 'RX_OCR', 'V+_OCR'])
terminal('J2', 'BIOSHUTTER', 4.5, 22.5, ['V+_SHUT', 'GND'])
terminal('J3', 'RELE_EXT', 4.5, 32.0,
         ['12V', 'VCC_RELE', 'GND', 'RELE1', 'RELE2', 'NO1', 'NO2'])
terminal('J4', 'BAT_12V', 4.5, 70.0, ['12V_IN', 'GND'])
# Jumpers 3 pines: 1-2 = por relé, 2-3 = directo de 12 V (pruebas sin relé)
header_v('JP1', 'OCR_PWR', 11.0, 33.0, ['NO1', 'V+_OCR', '12V'], h=2.5)
header_v('JP2', 'SHUT_PWR', 11.0, 41.0, ['NO2', 'V+_SHUT', '12V'], h=2.5)
header_v('JP3', 'RELE_VCC', 11.0, 49.0, ['+5V', 'VCC_RELE', '12V'], h=2.5)

# --- MAX3232 (DIP-16 300 mil) + capacitores --------------------------------
# Vista superior, muesca a la izquierda: fila inferior pines 1..8 (izq→der),
# fila superior pines 16..9 (izq→der).
mx, my = 16.0, 15.62
max_nets = {1: 'C1+', 2: 'V+', 3: 'C1-', 4: 'C2+', 5: 'C2-', 6: 'V-',
            7: None, 8: None, 9: None, 10: 'GND', 11: 'OCR_TXD', 12: 'OCR_RXD',
            13: 'TX_OCR', 14: 'RX_OCR', 15: 'GND', 16: 'VE'}
pads = []
for i in range(8):
    pads.append((str(1 + i), P * i, 0.0, N[max_nets[1 + i]] if max_nets[1 + i] else 0,
                 'rect_v' if i == 0 else 'ov_v'))
    pin = 16 - i
    pads.append((str(pin), P * i, -7.62, N[max_nets[pin]] if max_nets[pin] else 0, 'ov_v'))
part('U1', 'MAX3232', mx, my, pads,
     boxes=[(-1.3, -6.6, P * 7 + 1.3, -1.0, 0, 4.5, DARK)])


def cap(ref, x, y, a, b, vertical=False):
    dx, dy = (0, 5.08) if vertical else (5.08, 0)
    part(ref, '100n', x, y, [('1', 0, 0, N[a], 'cap'), ('2', dx, dy, N[b], 'cap')],
         boxes=[(dx / 2 - (2.5 if dx else 1.25), dy / 2 - (1.25 if dx else 2.5),
                 dx / 2 + (2.5 if dx else 1.25), dy / 2 + (1.25 if dx else 2.5), 0, 6, YELLOW)])


cap('C1', 13.5, 3.0, 'C1+', 'C1-')
cap('C2', 21.5, 3.0, 'C2+', 'C2-')
cap('C3', 29.5, 3.0, 'V+', 'GND')
cap('C4', 37.5, 3.0, 'V-', 'GND')
cap('C5', 40.0, 8.0, 'VE', 'GND', vertical=True)

# --- Heltec V4 (USB-C hacia el borde derecho) ------------------------------
# Rotada: J2 fila superior, J3 fila inferior, pin 1 del lado del USB (derecha).
HW, HH = 51.8, 25.5
hx0, hy0 = 46.75, 2.2
j2 = {1: 'GND', 2: '+5V_H', 3: 'VE', 4: 'VE', 12: 'GPS_RX', 13: 'SDA', 14: 'SCL'}
j3 = {1: 'GND', 7: 'SD_CS', 8: 'SD_MOSI', 9: 'SD_MISO', 10: 'SD_SCK', 11: 'GPS_TX',
      14: 'RELE2', 15: 'RELE1', 16: 'OCR_TXD', 17: 'OCR_RXD'}
pads = []
for n in range(1, 19):
    x = HW - 1.55 - P * (n - 1)
    pads.append((f'A{n}', x, 1.32, N[j2[n]] if n in j2 else 0, 'rect_v' if n == 1 else 'ov_v'))
    pads.append((f'B{n}', x, 1.32 + 22.86, N[j3[n]] if n in j3 else 0, 'rect_v' if n == 1 else 'ov_v'))
xa, xb = HW - 1.55 - P * 17 - 1.27, HW - 1.55 + 1.27
part('U2', 'HELTEC_V4', hx0, hy0, pads, boxes=[
    (xa, 0.05, xb, 2.59, 0, SOCKET_H, BLACK),
    (xa, 22.91, xb, 25.45, 0, SOCKET_H, BLACK),
    (0, 0, HW, HH, MOD_ON_SOCKET, MOD_ON_SOCKET + 1.6, DARK),
    (14, 4, 40, 21, MOD_ON_SOCKET + 1.6, MOD_ON_SOCKET + 3.6, BLACK),     # OLED
    (HW - 7.5, 8.5, HW + 0.8, 17.0, MOD_ON_SOCKET + 1.6, MOD_ON_SOCKET + 4.8, SILVER),  # USB-C
])

# --- RTC DS3231 (ZS-042): fila de 6 pines a 6.95 mm del borde del módulo ---
rx0, ry0 = 22.45, 31.0
rtc_nets = ['GND', 'VE', 'SDA', 'SCL', None, None]       # pin1 abajo
pads = [(str(i + 1), -6.95, 4.7 + P * (5 - i), N[a] if a else 0,
         'rect_h' if i == 0 else 'ov_h') for i, a in enumerate(rtc_nets)]
part('U3', 'RTC_DS3231', rx0, ry0, pads, boxes=[
    (-8.2, 3.4, -5.7, 19.0, 0, SOCKET_H, BLACK),
    (0, 0, 38.1, 22.1, 6.0, 7.6, BLUE),
    (12, 3, 34, 19, 2.8, 6.0, SILVER),                    # CR2032 debajo
    (3, 4, 14, 12, 7.6, 9.6, BLACK)])

# --- IMUs: ICM-20689 y GY-511, mismo eje X/Y, enchufados en tiras hembra ---
ix0, iy0 = 62.5, 32.0
icm = (row(4, 2.25, 1.6, [N['ICM_INT'], 0, 0, N['GND']]) +   # pines 2-3: ver módulo (AD0→VE)
       row(4, 2.25, 13.0, [N['VE'], N['GND'], N['SCL'], N['SDA']], first=5))
part('U4', 'ICM-20689', ix0, iy0, icm, boxes=[
    (0.9, 0.3, 11.2, 2.9, 0, SOCKET_H, BLACK),
    (0.9, 11.7, 11.2, 14.3, 0, SOCKET_H, BLACK),
    (0, 0, 12.1, 15.1, MOD_ON_SOCKET, MOD_ON_SOCKET + 1.6, BLUE)])
gx0, gy0 = 77.6, 32.0
gy = row(8, 1.35, 1.55, [0, 0, 0, N['SDA'], N['SCL'], N['GND'], N['VE'], 0])
part('U5', 'GY-511', gx0, gy0, gy, boxes=[
    (0.1, 0.3, 19.4, 2.8, 0, SOCKET_H, BLACK),
    (0, 0, 20.6, 14.6, MOD_ON_SOCKET, MOD_ON_SOCKET + 1.6, BLUE)])

# --- GPS (NEO-6M por cable) y I2C auxiliar (BNO085 si llega) --------------
header_h('J5', 'GPS', 64.0, 50.5, ['VE', 'GPS_RX', 'GPS_TX', 'GND'], h=8.5)
header_h('J6', 'I2C_AUX', 78.0, 50.5, ['VE', 'GND', 'SCL', 'SDA'], h=8.5)

# --- Buck (MP1584, 22 x 17) ------------------------------------------------
bx0, by0 = 12.0, 58.0
part('U6', 'BUCK_5V', bx0, by0, [
    ('1', 2.05, 2.01, N['+5V'], 'ov_h'), ('2', 2.05, 4.55, N['+5V'], 'ov_h'),
    ('3', 20.05, 1.77, N['GND'], 'ov_h'), ('4', 20.05, 4.32, N['GND'], 'ov_h'),
    ('5', 2.05, 12.77, N['12V'], 'ov_h'), ('6', 2.05, 15.31, N['12V'], 'ov_h'),
    ('7', 20.05, 12.77, N['GND'], 'ov_h'), ('8', 20.05, 15.31, N['GND'], 'ov_h')],
    boxes=[(0, 0, 22.1, 17.1, 3.0, 4.6, BLUE), (6, 4, 14, 12, 4.6, 8.6, DARK)])

# --- Protección: fusible, diodo serie, diodo a la Heltec (axiales parados) --
def axial_v(ref, val, x, y, a, b, color):
    part(ref, val, x, y, [('1', 0, 0, N[a], 'big'), ('2', 0, 5.08, N[b], 'big')],
         boxes=[(-1.8, -1.8, 1.8, 1.8, 0, 11, color)])


# 12V_IN → F1 → F_OUT → D1 (polaridad) → 12V ; buck 5V → D2 → pin 5V Heltec
axial_v('F1', 'FUSE_1A', 38.0, 60.0, '12V_IN', 'F_OUT', TAN)
axial_v('D1', '1N5819', 38.0, 70.0, 'F_OUT', '12V', BLACK)
axial_v('D2', '1N5819', 45.0, 60.0, '+5V', '+5V_H', BLACK)

# --- MicroSD (Catalex, 42 x 24, 5 V): tira 90° a 3.95 mm, ranura al borde --
sx0, sy0 = 58.0, 56.0
sd_nets = ['CS', 'SCK', 'MOSI', 'MISO', 'VCC', 'GND']           # de arriba a abajo
mapn = {'CS': 'SD_CS', 'SCK': 'SD_SCK', 'MOSI': 'SD_MOSI', 'MISO': 'SD_MISO',
        'VCC': '+5V', 'GND': 'GND'}
pads = [(str(i + 1), -3.95, 6.01 + P * i, N[mapn[a]], 'rect_h' if i == 0 else 'ov_h')
        for i, a in enumerate(sd_nets)]
part('U7', 'MICROSD', sx0, sy0, pads,
     boxes=[(-5.2, 4.7, -2.7, 20.0, 0, 8.5, BLACK),
            (0, 0, 42.1, 24.1, 3.0, 4.6, BLUE),
            (28, 5, 42.6, 19, 4.6, 7.0, SILVER)],
     holes=[(2.05, 2.05, 2.2), (40.05, 2.05, 2.2), (2.05, 22.05, 2.2), (40.05, 22.05, 2.2)])

# Agujeros de montaje M3 de la placa
MOUNTING = [(4.0, 2.6), (3.5, 78.5), (44.0, 29.35), (97.5, 51.5)]

# ---------------------------------------------------------------- emisión
PAD = {'ov_v': ('oval', 1.8, 3.0, 1.0), 'ov_h': ('oval', 3.0, 1.8, 1.0),
       'rect_v': ('rect', 1.8, 3.0, 1.0), 'rect_h': ('rect', 3.0, 1.8, 1.0),
       'big': ('circle', 2.6, 2.6, 1.2), 'cap': ('circle', 2.0, 2.0, 0.8)}


def u():
    return f'(tstamp "{uuid.uuid4()}")'


def wrl(path, boxes):
    """Cajas en VRML (unidad KiCad = 0.1 pulgada); Y invertida en 3D."""
    k = 1 / 2.54
    out = ['#VRML V2.0 utf8']
    for x0, y0, x1, y1, z0, z1, (r, g, b) in boxes:
        pts = [(x, -y, z) for z in (z0, z1) for (x, y) in
               ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        pts = ', '.join(f'{x*k:.4f} {y*k:.4f} {z*k:.4f}' for x, y, z in pts)
        faces = '0,1,2,3,-1, 7,6,5,4,-1, 0,4,5,1,-1, 1,5,6,2,-1, 2,6,7,3,-1, 3,7,4,0,-1'
        out.append(f'Shape {{ appearance Appearance {{ material Material {{ '
                   f'diffuseColor {r} {g} {b} }} }} geometry IndexedFaceSet {{ '
                   f'solid FALSE coord Coordinate {{ point [ {pts} ] }} '
                   f'coordIndex [ {faces} ] }} }}')
    open(path, 'w').write('\n'.join(out) + '\n')


def emit_part(p):
    s = f'  (footprint "nodo_a:{p["val"] or p["ref"]}" (layer "F.Cu") {u()} (at {p["x"]} {p["y"]})\n'
    s += '    (attr through_hole)\n'
    bx = [b[:4] for b in p['boxes']] or [(-2, -2, 2, 2)]
    x0 = min(b[0] for b in bx); y0 = min(b[1] for b in bx)
    x1 = max(b[2] for b in bx); y1 = max(b[3] for b in bx)
    s += (f'    (fp_text reference "{p["ref"]}" (at {(x0+x1)/2:.2f} {(y0+y1)/2:.2f}) '
          f'(layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))) {u()})\n')
    s += (f'    (fp_text value "{p["val"]}" (at {(x0+x1)/2:.2f} {(y0+y1)/2+1.5:.2f}) '
          f'(layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))) {u()})\n')
    s += (f'    (fp_rect (start {x0} {y0}) (end {x1} {y1}) (stroke (width 0.12) '
          f'(type solid)) (fill none) (layer "F.Fab") {u()})\n')
    for num, dx, dy, net, kind in p['pads']:
        shape, w, h, drill = PAD[kind]
        netref = f' (net {net} "{NETS[net]}")' if net else ''
        s += (f'    (pad "{num}" thru_hole {shape} (at {dx} {dy}) (size {w} {h}) '
              f'(drill {drill}) (layers "*.Cu" "*.Mask"){netref} {u()})\n')
    for dx, dy, d in p['holes']:
        s += (f'    (pad "" np_thru_hole circle (at {dx} {dy}) (size {d} {d}) '
              f'(drill {d}) (layers "*.Cu" "*.Mask") {u()})\n')
    if p['boxes']:
        path = os.path.join(D3, f'{p["ref"]}.wrl')
        wrl(path, p['boxes'])
        s += (f'    (model "{path}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) '
              f'(rotate (xyz 0 0 0)))\n')
    return s + '  )\n'


def emit_hole(x, y):
    return (f'  (footprint "nodo_a:M3" (layer "F.Cu") {u()} (at {x} {y})\n'
            f'    (attr through_hole exclude_from_bom)\n'
            f'    (pad "" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) '
            f'(layers "*.Cu" "*.Mask") {u()})\n  )\n')


def emit_edge():
    c = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H)]
    return ''.join(f'  (gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) '
                   f'(layer "Edge.Cuts") (width 0.1) {u()})\n'
                   for a, b in zip(c, c[1:] + c[:1]))


HEADER = '''(kicad_pcb (version 20221018) (generator nodo_a)
  (general (thickness 1.6))
  (paper "A4")
  (layers
    (0 "F.Cu" signal) (31 "B.Cu" signal)
    (36 "B.SilkS" user) (37 "F.SilkS" user) (38 "B.Mask" user) (39 "F.Mask" user)
    (44 "Edge.Cuts" user) (46 "B.CrtYd" user) (47 "F.CrtYd" user)
    (48 "B.Fab" user) (49 "F.Fab" user)
  )
  (setup (pad_to_mask_clearance 0))
'''


def chequeo():
    """Choques 3D entre cajas de piezas distintas, y cajas fuera de la placa."""
    errs = []
    absb = []
    for p in PARTS:
        for b in p['boxes']:
            absb.append((p['ref'], b[0] + p['x'], b[1] + p['y'], b[2] + p['x'],
                         b[3] + p['y'], b[4], b[5]))
    for i, a in enumerate(absb):
        for b in absb[i + 1:]:
            if a[0] == b[0]:
                continue
            if (a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4]
                    and a[5] < b[6] and b[5] < a[6]):
                errs.append(f'choque {a[0]} / {b[0]}')
    for r, x0, y0, x1, y1, z0, z1 in absb:
        if (x0 < -0.01 or y0 < -0.01 or x1 > BOARD_W + 1.0 or y1 > BOARD_H + 0.01):
            errs.append(f'{r} fuera de la placa ({x0:.1f},{y0:.1f})-({x1:.1f},{y1:.1f})')
    for hx, hy in MOUNTING:
        for r, x0, y0, x1, y1, z0, z1 in absb:
            if x0 - 2.0 < hx < x1 + 2.0 and y0 - 2.0 < hy < y1 + 2.0 and z0 < 3:
                errs.append(f'agujero M3 ({hx},{hy}) choca con {r}')
    return sorted(set(errs))


def main():
    out = HEADER + ''.join(f'  (net {i} "{n}")\n' for i, n in enumerate(NETS))
    out += ''.join(emit_part(p) for p in PARTS)
    out += ''.join(emit_hole(x, y) for x, y in MOUNTING)
    out += emit_edge() + ')\n'
    open(os.path.join(HERE, 'nodo_a.kicad_pcb'), 'w').write(out)
    zmax = max(b[5] for p in PARTS for b in p['boxes'])
    print(f'nodo_a.kicad_pcb: {len(PARTS)} piezas, placa {BOARD_W} x {BOARD_H} mm, '
          f'altura máx {zmax} mm')
    for e in chequeo():
        print('  !', e)


if __name__ == '__main__':
    main()
