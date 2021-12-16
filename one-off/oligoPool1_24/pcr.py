metadata = {"apiLevel": "2.6"}

# The following are fragments ranging from 500 - 800bp
csv = """E1	H9
E1	A10	
C1	G10	
D1	E1	
G1	E2	
G1	F2	
C1	H10	
C1	A12	
C1	D11	
E1	B9	
E1	C9	
D1	C3	
C1	B10	
D1	E4	
E1	D6	
E1	E6	
C1	B11	
F1	A2	
F1	B2	
E1	B10	
E1	C10	
F1	A12	
F1	B12	
F1	C12	
E1	B7	
E1	C7	
D1	F3	
D1	H2	
G1	D2	
C1	C11	
A1	A3	"""

# The following is the control oligo pool from IDT
idt = """D1\tC5
D1\tB5
C1\tG8
D1\tG1
C1\tH12
C1\tD9
C1\tB11
C1\tB10"""


def run(protocol):
    primer_plate = protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", 3)
    pcr = protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", 2)
    p20s = protocol.load_instrument("p20_single_gen2", "left", tip_racks=[protocol.load_labware("opentrons_96_filtertiprack_20ul", i) for i in [4]])
    p300s = protocol.load_instrument("p300_single_gen2", "right", tip_racks=[protocol.load_labware("opentrons_96_tiprack_300ul", 5)])

    tube_rack = protocol.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", 1)
    mm = tube_rack.wells_by_name()["A1"]
    op = tube_rack.wells_by_name()["B1"]
    ctrl = tube_rack.wells_by_name()["C1"]

    p300s.transfer(47, mm, pcr.wells()[:20])
    p300s.transfer(22, op, mm, mix_after=(8, 200), new_tip="always")
    # 4 from the basic fragments
    for i, row in enumerate(csv.split("\n")[:4]):
        row_split = row.split("\t")
        p20s.transfer(1, op, pcr.wells()[i], new_tip="always")
        p20s.transfer(1, primer_plate.wells_by_name()[row_split[0]], pcr.wells()[i], new_tip="always")
        p20s.transfer(1, primer_plate.wells_by_name()[row_split[1]], pcr.wells()[i], new_tip="always")

    # 8 controls from op
    for i, row in enumerate(idt.split("\n")):
        row_split = row.split("\t")
        p20s.transfer(1, op, pcr.wells()[i+4], new_tip="always")
        p20s.transfer(1, ctrl, pcr.wells()[i+12], new_tip="always")
        for j in [0,8]:
            p20s.transfer(1, primer_plate.wells_by_name()[row_split[0]], pcr.wells()[i+4+j], new_tip="always")
            p20s.transfer(1, primer_plate.wells_by_name()[row_split[1]], pcr.wells()[i+4+j], new_tip="always")

# name: 42 in: main
# 1. 95c 30s
# 2. 95c 15s
# 3. 50c 15s
# 4. 68c 20s
# 5. GOTO 2 30
# 6. 68c 600s
# 7. 4c 3600s
