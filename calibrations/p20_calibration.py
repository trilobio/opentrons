metadata = {"apiLevel": "2.9"}

def run(ctx):
    pcr96 = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "1")
    standard_plate = ctx.load_labware("nest_96_wellplate_200ul_flat","2")
    agar_plate = ctx.load_labware("biorad_96_wellplate_200ul_pcr", "3")
    deep_well = ctx.load_labware("nest_96_wellplate_2ml_deep", "4")
    reservoir12 = ctx.load_labware("nest_12_reservoir_15ml", "5")
    reservoir = ctx.load_labware("nest_1_reservoir_195ml", "6")
    temperature_module = ctx.load_module("temperature module", "7")
    temp_plate = temperature_module.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")

    tube_rack = ctx.load_labware("opentrons_24_tuberack_nest_1.5ml_snapcap", "8")

    tip_rack = ctx.load_labware("opentrons_96_filtertiprack_20ul","9")

    p20s = ctx.load_instrument("p20_single_gen2", "left", tip_racks=[tip_rack])
    p20m = ctx.load_instrument("p20_multi_gen2", "right", tip_racks=[tip_rack])

    for pipette in [p20s, p20m]:
        pipette.pick_up_tip()
        for labware in [pcr96, standard_plate, deep_well, reservoir12, reservoir, temp_plate]:
            pipette.aspirate(1, labware.wells_by_name()["A1"].bottom())
        pipette.return_tip()

    p20m.pick_up_tip()
    p20m.aspirate(1, agar_plate.wells_by_name()["A1"])
    p20m.return_tip()

    p20s.pick_up_tip()
    p20s.aspirate(1, tube_rack.wells_by_name()["A1"])
    p20s.return_tip()
