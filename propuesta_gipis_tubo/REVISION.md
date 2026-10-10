# PCB del nodo A (frame: OCR Lu 0099 + BioShutter + IMU)

Placa que diseña Juan Ignacio Figna Pasotti con Carlos De Marziani (hilo de mail
"Sobre esquemático OCR", 29/9 → 7/10/2026). Objetivo: tenerla para la visita de
CONAE + Frouin, 26–30 oct 2026 (ver vault `conae-campana-oct2026/`).

## Contenido

- `OCR_PCB_juan/` — clon de https://github.com/jifigna/OCR_PCB (KiCad 10). **No
  editar acá**: es el upstream de Juan, actualizar con `git -C OCR_PCB_juan pull`.
- `referencias_mail/` — imágenes del hilo:
  - `2026-10-01_juan_garabato_mano.png` — primer boceto a mano de Juan.
  - `2026-10-01_juan_diagrama_bloques.png` — qué va en la PCB y qué afuera.
  - `2026-10-07_carlos_compacta_sin_rele.png` — propuesta de Carlos 100×80, relé afuera.
  - `2026-10-07_carlos_compacta_rele_apilado.png` — ídem con relé apilado sobre el MAX3232.
  Las de Carlos son ilustraciones conceptuales (generadas), no placement real.
- `renders/` — render 3D, esquemático y reportes ERC/DRC del commit eeee71c (7/10).

## Estado del diseño de Juan (commit eeee71c, 2026-10-07)

Placa 120,5 × 108 mm, solo placement (sin rutear). Módulos dibujados como
rectángulos de serigrafía, sin modelo 3D → el render no muestra alturas.

Problemas del esquemático (revisión 2026-10-09):
1. I2C no llega a la Heltec: red `SDA`/`SCL` (GY-511, ICM, RTC) vs etiquetas
   `SDA_INC`/`SCL_INC` colgadas en J4/J5.
2. Sin 12 V a OCR ni BioShutter: `V+_OCR` y `V+_BIOSHUT` pasan por J17/J18, sin footprint.
3. INT del GY-511 y del ICM unidos en `INT_INCL` → un GPIO para cada uno.
4. Sección relé desconectada (INI1/INI2/5V/VCC/JD-VCC sin destino; J15/J16 sin footprint).
5. ICM-20689: J2.2/J2.3 sin conectar (¿CS, AD0?) → revisar pinout del módulo.
6. Footprints que no coinciden: J13 (4 pines → 1x06), J15 (3 pines → bornera de 2).

Para discutir: buck al pin 3V3 de la Heltec (choca con USB enchufado; mejor 5 V al
pin 5V), todo colgado de Vext (lo prende el firmware con GPIO36), zener de 3,3 V
en D2 (mejor 3,6 V).

## Diferencias con el plan de campaña (vault, nodo A)

El plan pide en el nodo A: SD + DS3231 + **GPS** + **IMU** + **ADS1115 (PAR 231)**.
La placa de Juan no tiene GPS ni ADS1115, y usa GY-511 (el clon da |acc| ≈ 0,83 g)
+ ICM-20689.

Decisiones de Pablo (2026-10-09):
- IMU: ICM-20689 (ya en el lab; los BNO085 vienen en envío y no se cuenta con ellos) + GY-511 para comparar.
- GPS: se agrega, pero es lo primero que se saca si hay que compactar.
- Sin ADS1115 ni BNO085: están en envío y pueden llegar tarde. El PAR va en el
  barco (nodo B), no en el frame → esta placa no necesita ADC.
- Fabricación: prototipadora de PCB del laboratorio desde Gerber → reglas de
  diseño de fresado. Marca LPKF (confirmada), probablemente ProtoMat serie S (modelo a confirmar);
  la placa de muestra es de una cara, solo aislación, pistas ~1,5–2 mm.

Pines ya validados en protoboard (ver `../README.md`): I2C en GPIO17/18 (bus del
OLED), relé BioShutter GPIO3, relé OCR GPIO4, UART OCR GPIO5/6. Nunca usar GPIO45/46.

## Propuesta GIPIS v0 — `nodo_a/` (2026-10-09)

Placa generada por código (`gen_board.py`, método EOLOVITA), `./make.sh` regenera
placa + renders 3D (`out/`) + DRC con reglas LPKF (1 cara B.Cu, pista 0,8, aislación
0,6, sin vías). **100 × 82 mm, altura máx ≈ 16 mm** (Heltec sobre tira hembra).
Estado: placement + netlist, DRC limpio salvo ruteo pendiente.

Cambios respecto de la placa de Juan:
- I2C sensores en GPIO47/48 (Wire1); 17/18 son el OLED y no salen al header.
- SD en GPIO39–42 (SCK/MISO/MOSI/CS, como EOLOVITA) y alimentada a **5 V** (Catalex).
- GPS NEO-6M por cable (J5: VCC RX TX GND), GPIO38 ← TX del GPS, GPIO33 → RX.
- Relé externo por bornera J3 (12V, VCC_RELE, GND, IN1=GPIO4 OCR, IN2=GPIO3 shutter,
  NO1, NO2) + jumpers JP1/JP2 (relé o 12 V directo) y JP3 (VCC del relé 5/12 V).
- Entrada 12 V → fusible → 1N5819 serie; buck 5 V → 1N5819 → pin 5V de la Heltec
  (no al 3V3); periféricos de 3,3 V desde Vext (GPIO36 en LOW).
- DIP-16 de 300 mil (Juan usaba 400 mil), sin zener; sin INT/SQW (polling).
- I2C auxiliar J6 para el BNO085 si llega.

Pendiente de confirmar con los módulos en mano: pinout del ICM-20689 (AD0 a VE →
0x69, porque el DS3231 usa 0x68), orden de pines del módulo SD, tipo de relé.

## Propuesta GIPIS v1 "tubo" — `nodo_a/` (2026-10-09, pablo-work)

La electrónica va **dentro de un tramo del frame (PVC 59 mm interior)**: no suma
sombra. Placa **199 × 48 mm**, doble faz sin metalizar; `gen_board.py` chequea
que todo entre en el caño (placa 9 mm por debajo del eje, altura máx 21 mm =
LM2596). v0 (100 × 82) archivada en `nodo_a/v0_100x82/`. Fotos de módulos con
calibre en `fotos_lab_20261009/`.

Orden a lo largo del caño: bornas (BAT 5.08 + OCR/shutter 3.5) → fusible/diodo →
buck LM2596T-ADJ discreto (stock del lab: hay el chip; L 47 µH, 1N5822, 220 µF ×2,
R 1k/3k3 → 5.3 V) → 2 relés SRD sueltos con NPN + 1N4148 (JP3 elige bobina 5/12 V;
sin jumpers de bypass) → MAX3232 → Heltec V4 con ICM-20689 y GY-511 al lado del
I2C → GPS (J5) e I2C aux (J6) → RTC ZS-042 + MicroSD HW-125 (5 V).

Ruteo (`route.py 80 puentes` + `plano_gnd.py`): **23 puentes de alambre arriba**, GND
como plano abajo. Pendiente en KiCad a mano: 3–4 conexiones sin rutear (+5V hacia
D2/SD/JP3, RX_OCR, una isla de GND en Q2) y ~14 angostamientos de Freerouting a
0.6 mm cerca de pines.

A confirmar antes de fresar: NO/NC del relé real, pinout del transistor (EBC),
inductor y Schottky disponibles, GY-511 (sin foto), cable del OCR.
