metadata = {"apiLevel": "2.0"} # tentative?

def run(protocol):
    # Please input 100-200fmol for R9 and 150-300fmol for R10
    # Init protocol with 47ul of DNA in A1 of the magdeck

    magnetic_module = protocol.load_module("magnetic module", 1)
    temperature_module = protocol.load_module("temperature module", 4)
    tube_rack = protocol.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", 2)

    mag = magnetic_module.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    tmp = temperature_module.load_labware("opentrons_24_aluminumblock_generic_2ml_screwcap")

    magnetic_module.disengage()
    temperature_module.set_temperature(8) # I set to 8 rather than 4 because it takes way longer to get down to 4

    ethanol = tube_rack.wells_by_name()["A1"] # 70% ethanol in 2mL tube
    water = tube_rack.wells_by_name()["B1"]
    elution_buffer = tube_rack.wells_by_name()["C1"]
    trash = tube_rack.wells_by_name()["D1"]

    dna_cs = tmp.wells_by_name()["A1"]
    end_prep_buffer = tmp.wells_by_name()["B1"]
    end_prep_enzyme = tmp.wells_by_name()["C1"]
    ampure_beads = tmp.wells_by_name()["D1"]
    ligation_buffer = tmp.wells_by_name()["A2"]
    quick_ligase = tmp.wells_by_name()["B2"]
    adapter_mix = tmp.wells_by_name()["C2"]
    short_fragment_buffer = tmp.wells_by_name()["D2"]
    output_tube = tmp.wells_by_name()["A3"] # Blank 1.5mL screw cap tube

    p20s = protocol.load_instrument("p20_single_gen2", "left", tip_racks=[protocol.load_labware("opentrons_96_filtertiprack_20ul", 3)])
    p300s = protocol.load_instrument("p300_single_gen2", "right", tip_racks=[protocol.load_labware("opentrons_96_tiprack_300ul", 5)])

    ### End prep and adapter
    end_prep_well = mag.wells_by_name()["A1"]
    adapter_well = mag.wells_by_name()["B1"]

    # End prep reaction
    p20s.transfer(7, end_prep_buffer, end_prep_well, mix_before=(3,20))
    p20s.transfer(3, end_prep_enzyme, end_prep_well)
    p20s.transfer(1, dna_cs, end_prep_well, mix_after=(5,20))
    protocol.delay(300)

    # Purify with beads
    p300s.transfer(60, ampure_beads, end_prep_well, mix_before=(5,100), mix_after=(5,60))
    protocol.delay(300)
    p300s.pick_up_tip()
    p300s.mix(5, 30, end_prep_well) # little extra mix
    p300s.drop_tip()
    magnetic_module.engage()
    protocol.delay(420) # opentrons docs require at least 7 min when >50ul
    p300s.transfer(200, end_prep_well, trash)
    for _ in range(0,2):
        p300s.pick_up_tip()
        p300s.aspirate(200, ethanol)
        p300s.dispense(200, end_prep_well)
        p300s.aspirate(200, end_prep_well)
        p300s.drop_tip()
    protocol.delay(90) # Since we can't pipette off residue, just assume 90s is enough to dry
    magnetic_module.disengage()
    p300s.transfer(61, water, end_prep_well, mix_after=(5,30))
    protocol.delay(120)
    magnetic_module.engage()
    protocol.delay(420) # opentrons docs require at least 7 min when >50ul
    p300s.transfer(60, end_prep_well, adapter_well)
    magnetic_module.disengage()

    # Adapter ligation
    p20s.transfer(10, quick_ligase, adapter_well)
    p20s.transfer(5, adapter_mix, adapter_well)
    p300s.flow_rate.aspirate = 25 # default 150
    p300s.flow_rate.dispense = 25 # default 300
    p300s.transfer(25, ligation_buffer, adapter_well, mix_before=(5,100), mix_after=(3,25))
    p300s.flow_rate.aspirate = 150 # default 150
    p300s.flow_rate.dispense = 300 # default 300
    protocol.delay(600) # 10 min wait
    p300s.transfer(40, ampure_beads, adapter_well, mix_before=(5,100), mix_after=(5,60))
    protocol.delay(300)
    magnetic_module.engage()
    protocol.delay(420)
    p300s.transfer(200, adapter_well, trash)
    for _ in range(0,2):
        magnetic_module.disengage()
        p300s.transfer(250, short_fragment_buffer, adapter_well, mix_after=(5,200))
        protocol.delay(10)
        magnetic_module.engage()
        protocol.delay(420)
        p300s.transfer(200, adapter_well, trash)
        p300s.transfer(200, adapter_well, trash)
    protocol.delay(90)
    magnetic_module.disengage()
    p20s.transfer(15, elution_buffer, adapter_well, mix_after=(3,5))
    protocol.delay(600)
    magnetic_module.engage()
    protocol.delay(300)
    p20s.transfer(15, adapter_well, output_tube)


