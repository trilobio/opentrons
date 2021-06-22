metadata = {"apiLevel": "2.0"} # tentative?


def run(protocol):
	# Setup labwares
    lb = protocol.load_labware("nest_1_reservoir_195ml", 1).wells_by_name()["A1"]
    agar_plate = protocol.load_labware("biorad_96_wellplate_200ul_pcr", 2)
    temperature_module = protocol.load_module("temperature module", 4)
    competent_cell_plate = temperature_module.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")

    tube_rack = protocol.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", 5)
    competent_cells_300ul = tube_rack.wells_by_name()["A1"]
    water = tube_rack.wells_by_name()["B1"]
    pUC19 = tube_rack.wells_by_name()["C1"]

    tip_rack = protocol.load_labware("opentrons_96_filtertiprack_20ul", "6")

    p20s = protocol.load_instrument("p20_single_gen2", "left", tip_racks=[tip_rack])
    p20m = protocol.load_instrument("p20_multi_gen2", "right", tip_racks=[tip_rack])

    # Lower temperature of temperature module
    temperature_module.set_temperature(8) # I set to 8 rather than 4 because it takes way longer to get down to 4

    # Transfer competent cells to temperature module
    tips_used = 0
    p20s.pick_up_tip()
    p20s.aspirate(5, competent_cells_300ul)
    for i in range(24):
        p20s.aspirate(10, competent_cells_300ul)
        p20s.dispense(10, competent_cell_plate.wells()[i])
    p20s.drop_tip()

    # Prepare DNA. NEB ships pUC19 with 1ug per ul. We're going for 256pg on the low end, doubling 8 times until 32768pg
    # We are assuming here we go from a stock solution of pUC19 of 100ng, or 100,000pg
    pUC19_stock = 100000
    dilution = pUC19_stock/32768
    initial_stock_to_add = 20/dilution # 20ul as the end quantity of how much we want per tube
    initial_water_to_add = 20 - initial_stock_to_add

    # Fill the first tube with initial_water_to_add and the rest of the tubes with 10ul
    # We are filling the last column of the competent cell plate
    p20s.pick_up_tip()
    p20s.aspirate(3, water)
    p20s.aspirate(initial_water_to_add, water)
    p20s.dispense(initial_water_to_add, competent_cell_plate.wells()[88])
    for i in range(1,8):
        p20s.aspirate(10, water)
        p20s.dispense(10, competent_cell_plate.wells()[88+i])
    p20s.drop_tip()

    # Move pUC19 to initial tube, mix, drop tip
    p20s.pick_up_tip()
    p20s.aspirate(initial_stock_to_add, pUC19)
    p20s.dispense(initial_stock_to_add, competent_cell_plate.wells()[88])
    p20s.mix(3, 10, competent_cell_plate.wells()[88])
    p20s.drop_tip()

    # Dilute 1/2
    p20s.pick_up_tip()
    for i in range(1,8):
        p20s.aspirate(10, competent_cell_plate.wells()[88+i-1])
        p20s.dispense(10, competent_cell_plate.wells()[88+i])
        p20s.mix(3, 10, competent_cell_plate.wells()[88+i])
    p20s.drop_tip()

    # Add to competent cells
    for i in range(0,2):
        p20m.pick_up_tip()
        p20m.transfer(1, competent_cell_plate.wells()[88], competent_cell_plate.wells()[i*8], mix_after=(3,3), new_tip='never')
        p20m.drop_tip()

    # Wait 15 minutes (in NEB they ask for 30 minutes, but that is pretty long)
    protocol.delay(900)

    # heat shock
    temperature_module.set_temperature(42)
    protocol.delay(10) # The ramp up and down will probably take a bit, so we're doing a short time here. Can be optimized later
    temperature_module.set_temperature(8)

    # Wait 5 minutes
    protocol.delay(300)

    # Start plating
    for i in range(0,3):
        for j in range(0,3):
            p20m.pick_up_tip()
            if j != 0: # First plating of each column does not need dilution
                p20m.transfer(7.5, lb, competent_cell_plate.rows()[0][i], mix_after=(2,5), new_tip='never')
            p20m.aspirate(7.5, competent_cell_plate.rows()[0][i])

            # Plate
            current_lane = (i*3)+j
            p20m.move_to(agar_plate.rows()[0][current_lane].top(4))
            p20m.dispense(6.5)
            p20m.move_to(agar_plate.rows()[0][current_lane].bottom())
            p20m.move_to(agar_plate.rows()[0][current_lane].top())
            p20m.drop_tip()

    # Deactivate temperature module
    temperature_module.deactivate()
