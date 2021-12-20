metadata = {"apiLevel": "2.6"}

def run(protocol):
    p20s = protocol.load_instrument("p20_single_gen2", "left", tip_racks=[protocol.load_labware("opentrons_96_filtertiprack_20ul", i) for i in [4]])
    p300s = protocol.load_instrument("p300_single_gen2", "right", tip_racks=[protocol.load_labware("opentrons_96_tiprack_300ul", i) for i in [5]])

    primers = protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", 1)
    working_stock = protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", 2)
    water = protocol.load_labware("nest_1_reservoir_195ml", 3).wells_by_name()["A1"]

    p300s.transfer(90, water, working_stock.wells())
    p20s.transfer(10, primers.wells(), working_stock.wells(), mix_after=(3,15), new_tip='always')
