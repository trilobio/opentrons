metadata = {"apiLevel": "2.6"}
# https://bomb.bio/wp-content/uploads/2018/09/5.1_BOMB_plasmid_DNA_extraction_V1.0.pdf

def run(protocol):
    p300s = protocol.load_instrument("p300_single_gen2", "right", tip_racks=[protocol.load_labware("opentrons_96_tiprack_300ul", i) for i in [2]])
    magnetic_module = protocol.load_module("magnetic module", 7)
    mag = magnetic_module.load_labware("nest_96_wellplate_2ml_deep")
    magnetic_module.disengage()
    w = mag.wells_by_name()["A1"]

    input_plate = protocol.load_labware("nest_96_wellplate_2ml_deep", 3)
    iw = input_plate.wells_by_name()["A1"]

    tube_rack = protocol.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", 11)
    output = tube_rack.wells_by_name()["A1"]
    p1 = tube_rack.wells_by_name()["B1"]
    p2 = tube_rack.wells_by_name()["C1"]
    n3 = tube_rack.wells_by_name()["D1"]
    water = tube_rack.wells_by_name()["A2"]
    beads = tube_rack.wells_by_name()["B2"]

    ethanol = protocol.load_labware("nest_1_reservoir_195ml", 1).wells_by_name()["A1"]
    trash = protocol.load_labware("nest_1_reservoir_195ml", 1).wells_by_name()["A1"]

    p300s.transfer(1500, iw, trash.top())
    p300s.transfer(250, p1, iw, mix_after=(5,100))
    p300s.transfer(250, p2, iw, mix_after=(5,200))
    protocol.delay(300)
    p300s.transfer(500, n3, iw, mix_after=(5,200))
    protocol.delay(300)
    protocol.pause("Remove and centrifuge in swing-out rotor for 20min, 2000g, rt")
    p300s.transfer(300, iw.bottom(5), w)
    p300s.transfer(300, ethanol, w, air_gap=50) 
    p300s.transfer(50, beads, w, mix_after=(8,200))
    protocol.delay(300)
    magnetic_module.engage()
    protocol.delay(300)
    p300s.transfer(800, w, trash)
    magnetic_module.disengage()
    p300s.transfer(300, iw.bottom(5), w)
    p300s.transfer(300, ethanol, w, air_gap=50)
    p300s.transfer(50, beads, w, mix_after=(8,200))
    protocol.delay(300)
    magnetic_module.engage()
    protocol.delay(300)
    p300s.transfer(800, w, trash)
    magnetic_module.disengage()
    for _, range(0,2):
        p300s.transfer(300, pe, w, mix_after=(5,200))
        magnetic_module.engage()
        protocol.delay(300)
        p300s.transfer(300, w, trash)
        magnetic_module.disengage()
    protocol.delay(1200) # dry
    protocol.transfer(40, water, w, mix_after=(5,25))
    magnetic_module.engage()
    protocol.transfer(40, w.bottom(1), output)






