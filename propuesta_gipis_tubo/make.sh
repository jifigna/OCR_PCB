#!/bin/bash
# Nodo A — generar placa → renders 3D → DRC (reglas LPKF en nodo_a.kicad_dru)
set -e
cd "$(dirname "$0")"
python3 gen_board.py
R='kicad-cli pcb render --quality high nodo_a.kicad_pcb'
$R --rotate '-55,0,20' --perspective --width 2000 --height 1000 -o out/iso_izq.png >/dev/null 2>&1
$R --rotate '-50,0,-25' --perspective --width 2000 --height 1000 -o out/iso.png >/dev/null 2>&1
$R --side top --width 2400 --height 700 -o out/top3d.png >/dev/null 2>&1
$R --rotate '-90,0,0' --zoom 1.3 --width 2400 --height 500 -o out/lateral.png >/dev/null 2>&1
kicad-cli pcb drc nodo_a.kicad_pcb -o out/drc.rpt --severity-error 2>/dev/null | tail -2
