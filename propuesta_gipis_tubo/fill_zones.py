#!/usr/bin/env python3
"""Rellena las zonas de cobre del board y lo guarda (pcbnew headless)."""
import pcbnew

board = pcbnew.LoadBoard('nodo_a.kicad_pcb')
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard('nodo_a.kicad_pcb', board)
print('zonas rellenas y guardadas')
