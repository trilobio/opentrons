metadata = {"apiLevel": "2.6"}

samples = 2

def run(protocol):
    p20s = protocol.load_instrument("p20_single_gen2", "left", tip_racks=[protocol.load_labware("opentrons_96_filtertiprack_20ul", i) for i in [11]])

    temperature_module = protocol.load_module("temperature module", 10)
    tmp = temperature_module.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    assemblies = protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", 5)

    tube_rack = protocol.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", 8)
    comp_cells = tube_rack.wells_by_name()["A1"]
    water = tube_rack.wells_by_name()["B1"]
    puc19 = tube_rack.wells_by_name()["C1"]
    agar_plate = protocol.load_labware("biorad_96_wellplate_200ul_pcr", 4)

    temperature_module.set_temperature(8)
    p20s.transfer(15, comp_cells, tmp.wells()[:samples+1])
    p20s.transfer(1, assemblies.wells()[:samples], tmp.wells()[:samples], new_tip='always')
    p20s.transfer(1, puc19, tmp.wells()[samples])
    protocol.delay(900)
    temperature_module.set_temperature(42)
    protocol.delay(10)
    temperature_module.set_temperature(8)
    protocol.delay(300)
   
    w = ["{}{}".format(j, k + (i*3)) for i in range(0,4) for j in "ABCDEFGH" for k in range(1,4)]
    i = 0
    for well in tmp.wells()[:samples+1]:
        for j in range(0,3):
            t = agar_plate.wells_by_name()[w[i]]
            i+=1
            p20s.pick_up_tip()
            if j != 0:
                p20s.transfer(7.5, water, well, new_tip='never')
            p20s.mix(2,4,well)
            p20s.aspirate(7.5, well)
            p20s.move_to(t.top(6))
            p20s.dispense(6.5)
            p20s.move_to(t.bottom())
            p20s.move_to(t.top())
            p20s.drop_tip()
    temperature_module.deactivate()


