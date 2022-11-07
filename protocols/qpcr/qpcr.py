metadata = {"apiLevel": "2.0"}

# For running standard qPCRs on the chai machine
def run(protocol):
    
    tube_rack = protocol.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", 3)
    input_plate = protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", 5) # calibrated to cyroking plates
    output_plate = protocol.load_labware("biorad_96_wellplate_200ul_pcr", 2) # calibrated to strip tubes on aluminum plate

    mm = tube_rack.wells_by_name()["A1"] # chai qPCR mastermix
    water = tube_rack.wells_by_name()["B1"] # good ole H2O

    template = input_plate.wells_by_name()["A1"] # pOpen_v3, 2ng/uL
    m13for = input_plate.wells_by_name()["B1"] # M13for, 10uM
    m13rev = input_plate.wells_by_name()["C1"] # M13rev, 10uM

    p20s = protocol.load_instrument("p20_single_gen2", "left", tip_racks=[protocol.load_labware("opentrons_96_filtertiprack_20ul", 6)])

    # A1: water
    # B1: mastermix + water
    # C1: mastermix + water + primer
    # D1: mastermix + water + template
    #
    # E1: std
    # F1: std
    # G1: std
    # H1: std
    #
    # 20uL volume

    ctrl_1 = output_plate.wells_by_name()["A1"]
    ctrl_2 = output_plate.wells_by_name()["B1"]
    ctrl_3 = output_plate.wells_by_name()["C1"]
    ctrl_4 = output_plate.wells_by_name()["D1"]
    std_exp = [output_plate.wells_by_name()[x] for x in ["E1", "F1", "G1", "H1"]]

    # Add water
    p20s.pick_up_tip()
    p20s.transfer(20, water, ctrl_1, new_tip="never")
    p20s.transfer(8, water, ctrl_3, new_tip="never")
    p20s.transfer(9, water, ctrl_4, new_tip="never")
    p20s.transfer(10, water, [ctrl_2] + std_exp, new_tip="never")
    p20s.drop_tip()

    # Add everything else
    p20s.transfer(10, mm, [ctrl_2, ctrl_3, ctrl_4] + std_exp, new_tip="once") # mm
    [p20s.transfer(1, primer, [ctrl_3] + std_exp, new_tip="always") for primer in [m13for, m13rev]] # primers
    p20s.transfer(1, template, [ctrl_4] + std_exp, new_tip="always") # template
