#!/usr/bin/env python3
"""Nodo A (frame OCR Lu 0099) — generador del PCB, propuesta GIPIS v1 "tubo".

v1 (2026-10-09): placa larga y angosta para ir DENTRO de un tramo del frame
(PVC de 59 mm de diámetro interior), así la electrónica no suma sombra. La v0
de 100 x 82 está en v0_100x82/. Módulos medidos con calibre (fotos en
../fotos_lab_20261009/). Doble faz SIN metalizar (LPKF ProtoMat S63 del lab):
los zócalos se sueldan solo abajo, arriba solo puentes entre vías (route.py).

Eje X = a lo largo del caño, Y = a lo ancho. Origen arriba a la izquierda,
vista superior. Cada módulo lleva una caja 3D (VRML) con su altura sobre la placa.
"""

import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
D3 = os.path.join(HERE, '3d')

# ---------------------------------------------------------------- parámetros
BOARD_W, BOARD_H = 199.0, 48.0          # largo (X) x ancho (Y)
P = 2.54
SOCKET_H = 8.5          # tira hembra vertical 2.54
MOD_ON_SOCKET = 11.0    # base del módulo enchufado (hembra + plástico del macho)

# Caño: radio interior 29.5 mm con 1 mm de margen; la cara de arriba de la
# placa queda TUBE_D mm por debajo del eje del caño. Abajo: 1.6 de placa + 3 de soldaduras.
TUBE_R, TUBE_D, BOTTOM = 29.5 - 1.0, 9.0, 1.6 + 3.0

# ---------------------------------------------------------------- nets
NETS = ["", "GND", "12V_IN", "F_OUT", "12V", "SW", "FB", "+5V", "+5V_H", "VE",
        "SDA", "SCL", "SD_CS", "SD_MOSI", "SD_MISO", "SD_SCK",
        "GPS_TX", "GPS_RX", "OCR_TXD", "OCR_RXD", "TX_OCR", "RX_OCR",
        "RELE1", "RELE2", "B1", "B2", "K1", "K2", "VCC_RELE",
        "V+_OCR", "V+_SHUT", "C1+", "C1-", "C2+", "C2-", "V+", "V-"]
N = {n: i for i, n in enumerate(NETS)}

# ---------------------------------------------------------------- piezas
# Una pieza: dict(ref, val, x, y, pads=[(num, dx, dy, net, kind)], boxes, holes)
#   kind: 'ov_v' oval alargado en Y (fila horizontal), 'ov_h' alargado en X
#         (fila vertical), 'rect_v'/'rect_h' pin 1, 'big' bornera/diodo,
#         'big2' diodo de 3 A, 'cap' componente chico
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
CYAN, COPPER = (.2, .5, .8), (.7, .4, .2)


def terminal(ref, val, x, y, nets, pitch=3.5):
    """Bornera enchufable vertical (macho en placa), pines hacia abajo (Y).
    Stock del lab: verdes de 5.08 (2 y 3 polos) y de 3.5 (hasta 12 polos)."""
    n = len(nets)
    pads = row(n, 0, 0, [N[a] for a in nets], horizontal=False, pitch=pitch, kind='big')
    half = pitch / 2
    part(ref, val, x, y, pads,
         boxes=[(-3.5, -half, 3.5, pitch * n - half, 0, 12, GREEN)])


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


def axial_v(ref, val, x, y, a, b, color, kind='big', h=11):
    """Axial parado, patas en Y separadas 5.08."""
    part(ref, val, x, y, [('1', 0, 0, N[a], kind), ('2', 0, 5.08, N[b], kind)],
         boxes=[(-1.8, -1.8, 1.8, 1.8, 0, h, color)])


def axial_h(ref, val, x, y, a, b, color, kind='cap', h=9):
    """Axial parado, patas en X separadas 5.08."""
    part(ref, val, x, y, [('1', 0, 0, N[a], kind), ('2', 5.08, 0, N[b], kind)],
         boxes=[(-1.3, -1.3, 1.3, 1.3, 0, h, color)])


def radial(ref, val, x, y, a, b, d, pitch, h, color=BLACK):
    """Electrolítico / inductor radial: pin 1 (+) a la izquierda."""
    part(ref, val, x, y, [('1', -pitch / 2, 0, N[a], 'big'), ('2', pitch / 2, 0, N[b], 'big')],
         boxes=[(-d / 2, -d / 2, d / 2, d / 2, 0.5, h, color)])


# === Bornes (punta izquierda del caño: entran los cables por el prensacable) ==
terminal('J4', 'BAT_12V', 4.5, 4.0, ['12V_IN', 'GND'], pitch=5.08)
terminal('J1', 'OCR_SHUT', 4.5, 17.0,
         ['V+_OCR', 'GND', 'TX_OCR', 'RX_OCR', 'V+_SHUT', 'GND'])

# === Entrada 12 V: fusible + diodo serie ====================================
axial_v('F1', 'FUSE_1A', 12.0, 3.0, '12V_IN', 'F_OUT', TAN)
axial_v('D1', '1N5819', 17.5, 3.0, 'F_OUT', '12V', BLACK)

# === Buck LM2596T-ADJ (TO-220-5 vertical, patas alternadas 3.4 x 3.7) =======
# 1 VIN, 2 OUT(SW), 3 GND, 4 FB, 5 ON/OFF (a GND = encendido). Vout =
# 1.23 x (1 + R2/R1) = 1.23 x (1 + 3k3/1k) = 5.3 V (D2 deja ~5.0 en la Heltec).
radial('C6', '220u/35V', 25.0, 7.0, '12V', 'GND', 8.0, 3.5, 12)
ux, uy = 31.5, 4.0
lm = {1: '12V', 2: 'SW', 3: 'GND', 4: 'FB', 5: 'GND'}
pads = [(str(n), 1.7 * (n - 1), 0.0 if n % 2 else 3.7, N[lm[n]], 'big') for n in range(1, 6)]
part('U6', 'LM2596T-ADJ', ux, uy, pads,
     boxes=[(-1.6, -2.6, 8.4, 1.9, 3.0, 21.0, DARK)])
axial_v('D3', '1N5822', 44.0, 2.5, 'SW', 'GND', BLACK, kind='big2')   # cátodo a SW
radial('L1', '47uH', 34.0, 17.0, 'SW', '+5V', 12.0, 5.0, 10, COPPER)
radial('C7', '220u/10V', 45.0, 17.0, '+5V', 'GND', 8.0, 3.5, 12)
axial_v('R2', '3k3', 20.5, 13.0, '+5V', 'FB', TAN, kind='cap', h=9)
axial_v('R1', '1k', 24.5, 13.0, 'FB', 'GND', TAN, kind='cap', h=9)

# === Relés SRD sueltos (OCR y BioShutter) con NPN + diodo ===================
# Footprint SANYOU/Songle SRD: COM (0,0); bobina (1.95, ±6); contactos (14.2, ±6).
# OJO: NO/NC asumido (pad 4 = NO); verificar con el relé real antes de fresar.
def relay(ref, x, y, coil_hi, coil_lo, com, no):
    pads = [('1', 0, 0, N[com], 'big'),
            ('2', 1.95, -5.95, N[coil_hi], 'big'),
            ('5', 1.95, 6.05, N[coil_lo], 'big'),
            ('3', 14.15, -5.95, 0, 'big'),
            ('4', 14.2, 6.05, N[no], 'big')]
    part(ref, 'SRD-xxVDC', x, y, pads,
         boxes=[(-2.45, -7.75, 16.65, 7.75, 0, 15.5, CYAN)])


relay('K1', 12.5, 32.5, 'VCC_RELE', 'K1', '12V', 'V+_OCR')
relay('K2', 33.5, 32.5, 'VCC_RELE', 'K2', '12V', 'V+_SHUT')


def driver(n, x, y):
    """NPN TO-92 (2N2222/2N3904: E B C) + R base 1k + 1N4148 en la bobina.
    La pata del medio (base) se dobla hacia arriba: pad a 2.54 de la fila,
    así la pista de la base no tiene que pasar entre E y C."""
    gp, b, k = f'RELE{n}', f'B{n}', f'K{n}'
    part(f'Q{n}', '2N2222', x, y,
         [('1', 0, 0, N['GND'], 'to92'), ('2', P, -P, N[b], 'to92'), ('3', 2 * P, 0, N[k], 'to92')],
         boxes=[(-0.8, -1.2, 5.9, 2.0, 0, 5.0, BLACK)])
    axial_h(f'R{n + 2}', '1k', x + 7.0, y - P, b, gp, TAN)   # base del lado del NPN
    axial_h(f'D{n + 3}', '1N4148', x + 17.0, y, k, 'VCC_RELE', (.85, .3, .2), kind='cap', h=6)


driver(1, 11.5, 44.5)
driver(2, 37.0, 44.5)

# Sin jumpers de bypass (v0 tenía JP1/JP2): para probar sin relé, puente de
# cable COM–NO. JP3 elige la tensión de bobina según el relé que haya (SRD-05/12).
header_v('JP3', 'RELE_VCC', 57.0, 26.0, ['+5V', 'VCC_RELE', '12V'], h=2.5)

# === MAX3232 (DIP-16 300 mil) + capacitores =================================
# Vista superior, muesca a la izquierda: fila inferior pines 1..8 (izq→der),
# fila superior pines 16..9 (izq→der).
mx, my = 64.0, 34.0
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


# C1..C4 van a los pines 1..6 (fila de abajo) → debajo del DIP; C5 al pin 16.
cap('C1', 62.0, 39.0, 'C1+', 'C1-')
cap('C2', 70.0, 39.0, 'C2+', 'C2-')
cap('C3', 62.0, 44.5, 'V+', 'GND')
cap('C4', 70.0, 44.5, 'V-', 'GND')
cap('C5', 61.0, 20.0, 'VE', 'GND')

# === Heltec V4 (USB-C hacia la derecha) =====================================
# Rotada: J2 fila de arriba, J3 fila de abajo, pin 1 del lado del USB.
# Filas a 22.86 mm (medido con calibre en el lab, 2026-10-09).
HW, HH = 51.8, 25.5
hx0, hy0 = 84.0, 19.5
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

# === IMUs sobre la Heltec (lado del I2C), mismos ejes X/Y ===================
# ICM-20689 (15 x 11.4, castellado, 2 columnas de 4 a 12.7 mm), CHIP ARRIBA:
# columna izq VCC GND SCL SDA, columna der INT DA CL AD0 (AD0 a VE → 0x69,
# el DS3231 es 0x68). INT, DA y CL sin conectar (polling).
ix0, iy0 = 88.0, 3.0
icm = (row(4, 1.15, 1.89, [N['VE'], N['GND'], N['SCL'], N['SDA']], horizontal=False) +
       row(4, 13.85, 1.89, [0, 0, 0, N['VE']], horizontal=False, first=5))
part('U4', 'ICM-20689', ix0, iy0, icm, boxes=[
    (-0.12, 0.62, 2.42, 10.78, 0, SOCKET_H, BLACK),
    (12.58, 0.62, 15.12, 10.78, 0, SOCKET_H, BLACK),
    (0, 0, 15.0, 11.4, MOD_ON_SOCKET, MOD_ON_SOCKET + 1.6, (.1, .1, .1))])
gx0, gy0 = 106.0, 1.5
gy = row(8, 1.35, 1.55, [0, 0, 0, N['SDA'], N['SCL'], N['GND'], N['VE'], 0])
part('U5', 'GY-511', gx0, gy0, gy, boxes=[
    (0.1, 0.3, 19.4, 2.8, 0, SOCKET_H, BLACK),
    (0, 0, 20.6, 14.6, MOD_ON_SOCKET, MOD_ON_SOCKET + 1.6, BLUE)])

# 5 V a la Heltec por diodo (no por el pin 3V3)
axial_v('D2', '1N5819', 130.0, 4.0, '+5V', '+5V_H', BLACK)

# === GPS (HW-248 NEO-6M por cable dupont) e I2C auxiliar (BNO085 si llega) ==
# Espacio libre entre la Heltec y el RTC/SD: lugar para la ficha USB-C.
# GPS a la altura del medio de la Heltec: TX sale de la fila J3 y RX de la J2.
header_v('J5', 'GPS', 140.0, 22.0, ['VE', 'GPS_RX', 'GPS_TX', 'GND'], h=8.5)
header_h('J6', 'I2C_AUX', 138.5, 9.5, ['VE', 'GND', 'SCL', 'SDA'], h=8.5)

# === RTC ZS-042 (DS3231 + EEPROM 0x57), plano con la tira a 90° hacia abajo ==
# Tira: 32K SQW SCL SDA VCC GND. Sacar el diodo/resistencia de carga si
# lleva CR2032 común (no recargable).
rx0, ry0 = 158.2, 0.8
rtc_nets = ['GND', 'VE', 'SDA', 'SCL', None, None]       # pin1 abajo
pads = [(str(i + 1), -6.95, 4.7 + P * (5 - i), N[a] if a else 0,
         'rect_h' if i == 0 else 'ov_h') for i, a in enumerate(rtc_nets)]
part('U3', 'RTC_DS3231', rx0, ry0, pads, boxes=[
    (-8.2, 3.4, -5.7, 19.0, 0, SOCKET_H, BLACK),
    (0, 0, 38.1, 22.1, 6.0, 7.6, BLUE),
    (12, 3, 34, 19, 2.8, 6.0, SILVER),                    # CR2032 debajo
    (3, 4, 14, 12, 7.6, 9.6, BLACK)])

# === MicroSD HW-125 (AMS1117 + 74LVC125 → va a 5 V), 42 x 24 ================
# Tira a 90°. Vista de componentes con la tira a la izquierda, de arriba a
# abajo: GND VCC MISO MOSI SCK CS (el dorso dice CS..GND de izq a der).
sx0, sy0 = 155.2, 23.4
sd_nets = ['GND', 'VCC', 'MISO', 'MOSI', 'SCK', 'CS']
mapn = {'CS': 'SD_CS', 'SCK': 'SD_SCK', 'MOSI': 'SD_MOSI', 'MISO': 'SD_MISO',
        'VCC': '+5V', 'GND': 'GND'}
pads = [(str(i + 1), -3.95, 6.01 + P * i, N[mapn[a]], 'rect_h' if i == 0 else 'ov_h')
        for i, a in enumerate(sd_nets)]
part('U7', 'MICROSD', sx0, sy0, pads,
     boxes=[(-5.2, 4.7, -2.7, 20.0, 0, 8.5, BLACK),
            (0, 0, 42.1, 24.1, 3.0, 4.6, BLUE),
            (28, 5, 42.6, 19, 4.6, 7.0, SILVER)],
     holes=[(2.05, 2.05, 2.2), (40.05, 2.05, 2.2), (2.05, 22.05, 2.2), (40.05, 22.05, 2.2)])

# Agujeros de montaje M3 (al trineo impreso que va dentro del caño)
MOUNTING = [(4.0, 44.5), (52.0, 4.0), (142.0, 44.5), (147.0, 17.0)]

# ---------------------------------------------------------------- emisión
PAD = {'ov_v': ('oval', 1.8, 3.0, 1.0), 'ov_h': ('oval', 3.0, 1.8, 1.0),
       'rect_v': ('rect', 1.8, 3.0, 1.0), 'rect_h': ('rect', 3.0, 1.8, 1.0),
       'big': ('circle', 2.6, 2.6, 1.2), 'big2': ('circle', 3.0, 3.0, 1.4),
       'cap': ('circle', 2.0, 2.0, 0.8),
       'to92': ('oval', 1.5, 2.4, 0.8)}


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
    # Envolvente del caño: sección circular, placa TUBE_D por debajo del eje
    for r, x0, y0, x1, y1, z0, z1 in absb:
        for yy in (y0, y1):
            for zz in (z1, -BOTTOM):
                dist = ((yy - BOARD_H / 2) ** 2 + (zz - TUBE_D) ** 2) ** 0.5
                if dist > TUBE_R:
                    errs.append(f'{r} no entra en el caño ({dist:.1f} > {TUBE_R} mm)')
    return sorted(set(errs))


def main():
    out = HEADER + ''.join(f'  (net {i} "{n}")\n' for i, n in enumerate(NETS))
    out += ''.join(emit_part(p) for p in PARTS)
    out += ''.join(emit_hole(x, y) for x, y in MOUNTING)
    out += emit_edge() + ')\n'
    open(os.path.join(HERE, 'nodo_a.kicad_pcb'), 'w').write(out)
    zmax = max(b[5] for p in PARTS for b in p['boxes'])
    print(f'nodo_a.kicad_pcb: {len(PARTS)} piezas, placa {BOARD_W} x {BOARD_H} mm, '
          f'altura máx {zmax} mm, caño Ø{2 * (TUBE_R + 1):.0f} mm')
    for e in chequeo():
        print('  !', e)


if __name__ == '__main__':
    main()
