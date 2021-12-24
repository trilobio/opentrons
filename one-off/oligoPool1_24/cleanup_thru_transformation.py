metadata = {"apiLevel": "2.6"}

bead_ratio = 1.8
sample_volume = 45
bead_volume = sample_volume * bead_ratio
total_cleanup_volume = bead_volume + sample_volume + 5

def run(protocol):
    p20s = protocol.load_instrument("p20_single_gen2", "left", tip_racks=[protocol.load_labware("opentrons_96_filtertiprack_20ul", i) for i in [1, 5, 9]])
    p300s = protocol.load_instrument("p300_single_gen2", "right", tip_racks=[protocol.load_labware("opentrons_96_tiprack_300ul", i) for i in [2, 6]])

    magnetic_module = protocol.load_module("magnetic module", 7)
    temperature_module = protocol.load_module("temperature module", 10)
    mag = magnetic_module.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    tmp = temperature_module.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    magnetic_module.disengage()

    tube_rack = protocol.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", 11)
    snapshot_post_cleanup = tube_rack.wells_by_name()["A1"]
    water = tube_rack.wells_by_name()["C1"]
    cleanup_and_assembly_control = tube_rack.wells_by_name()["A2"]
    goldengate_mm = tube_rack.wells_by_name()["B2"]
    vector = tube_rack.wells_by_name()["C2"]
    transformation_control = tube_rack.wells_by_name()["D2"]
    competent_cells = tube_rack.wells_by_name()["A3"]

    reagents = protocol.load_labware("nest_12_reservoir_15ml", 8)
    ethanol = reagents.wells_by_name()["A3"]
    mag_beads = reagents.wells_by_name()["A2"]
    waste = reagents.wells_by_name()["A1"]

    agar_plate = protocol.load_labware("biorad_96_wellplate_200ul_pcr", 4)

    ### ======= ###
    ### Cleanup ###
    ### ======= ###
    
    # Initialize with plate on mag deck. Transfer cleanup control to well 20
    # neg control 20
    # cleanup control 21
    # assembly control 22
    # transformation control 23
    p20s.transfer(9, cleanup_and_assembly_control, mag.wells()[21], new_tip='always') # 3x assembly control
    p20s.transfer(41, , mag.wells()[21], new_tip='always')
    p300s.transfer(bead_volume, mag_beads, mag.wells()[:22], mix_before=(5, 200), mix_after=(10, bead_volume/2), new_tip='always')
    protocol.delay(300)
    magnetic_module.engage()
    protocol.delay(120)

    # default 92.86
    p300s.flow_rate.aspirate = 25

    # Discard supernatant and wash
    p300s.transfer(total_cleanup_volume, mag.wells()[:22], waste, blow_out=True, new_tip='always')
    for _ in range(0,2):
        p300s.transfer(180, ethanol, mag.wells()[:22], air_gap=20, new_tip='always')
        # normally protocol.delay(60) but this transfer should take long enough to just continue from beginning
        p300s.transfer(180, mag.wells()[:22], waste, air_gap=20, new_tip='always')

    # Dry for 5 minutes and then disengage
    magnetic_module.disengage()

    # Add elution buffer, mix, output
    p20s.transfer(40, water, mag.wells()[:22], mix_after=(10, 10), new_tip='always')
    protocol.delay(300)
    magnetic_module.engage()
    protocol.delay(120)
    p20s.transfer(40, mag.wells()[:22], mag.wells()[24:46], blow_out=True, new_tip='always')

    # snapshot
    p300s.flow_rate.aspirate = 92.86
    p20s.transfer(10, water, snapshot_post_cleanup, new_tip='always')
    p20s.transfer(3, mag.wells()[24:46], snapshot_post_cleanup, new_tip='always')

    ### ========== ###
    ### GoldenGate ###
    ### ========== ###
    
    # Pause for adding GoldenGate mastermix, excluding the transformation control
    protocol.pause("Add GoldenGate mastermix")
    p20s.transfer(16, goldengate_mm, mag.wells()[48:71])
    p20s.transfer(1, vector, mag.wells()[48:71], new_tip='always')
    p20s.transfer(3, mag.wells()[24:46], mag.wells()[48:70], new_tip='always')
    p20s.transfer(3, cleanup_and_assembly_control, mag.wells()[70], new_tip='always')

    ### ========================== ###
    ### Transformation and plating ###
    ### ========================== ###

    # Pause for adding competent cells
    protocol.pause("Remove GoldenGate, incubate at 37 for 1hr, add plate back onto temperature module")
    temperature_module.set_temperature(8)
    p20s.transfer(15, competent_cells, tmp.wells()[72:])
    p20s.transfer(1, tmp.wells()[48:71], tmp.wells()[72:95], new_tip='always')
    p20s.transfer(1, transformation_control, tmp.wells()[95], new_tip='always')

    # Wait 15 minutes (NEB asks for 30min, but that is fairly long)
    protocol.delay(900)

    # heat shock
    temperature_module.set_temperature(42)
    protocol.delay(10) # The ramp up and down will probably take a bit, so we're doing a short time here. Can be optimized later
    temperature_module.set_temperature(8)

    # Wait 5 minutes
    protocol.delay(300)

    # Start plating
    offset = -3
    for i in range(72,96):
        well = tmp.wells()[i]
        if i%8 == 0:
            offset += 4
        for dilution_num in range(0,4):
            p20s.pick_up_tip()
            if dilution_num > 0: # Do dolution
                p20s.transfer(7.5, water, well, new_tip='never')
            p20s.mix(2, 5, well)
            p20s.aspirate(7.5, well)

            # Plate
            target_well = agar_plate.wells_by_name()["{}{}".format("ABCDEFGH"[i%8], offset+dilution_num)]
            p20s.move_to(target_well.top(4))
            p20s.dispense(6.5)
            p20s.move_to(target_well.bottom())
            p20s.move_to(target_well.top())
            p20s.drop_tip()

    # Deactivate temperature module
    temperature_module.deactivate()
    magnetic_module.disengage()
