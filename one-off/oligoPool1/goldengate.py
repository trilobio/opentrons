metadata = {"apiLevel": "2.0"}

def run(protocol):
    amplicons = protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", 1)
    gg = protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", 2)
    tube_rack = protocol.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", 3)
    p20s = protocol.load_instrument("p20_single_gen2", "left", tip_racks=[protocol.load_labware("opentrons_96_filtertiprack_20ul", 6)])

    p20s.transfer(18, tube_rack.wells_by_name()["A1"], gg.wells()[:32], blow_out=True)
    p20s.transfer(2, amplicons.wells()[:32], gg.wells()[:32], mix_after=(2,5))
