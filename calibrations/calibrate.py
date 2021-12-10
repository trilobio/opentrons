metadata = {"apiLevel": "2.0"}

def run(ctx):
    pcr96 = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "1")
    standard_plate = ctx.load_labware("nest_96_wellplate_200ul_flat","2")
    agar_plate = ctx.load_labware("biorad_96_wellplate_200ul_pcr", "3")
    deep_well = ctx.load_labware("usascientific_96_wellplate_2.4ml_deep", "4")
    strips = ctx.load_labware("corning_96_wellplate_360ul_flat", 5)
    #reservoir12 = ctx.load_labware("nest_12_reservoir_15ml", "5")
    reservoir = ctx.load_labware("nest_1_reservoir_195ml", "6")
    #temperature_module = ctx.load_module("temperature module", "7")
    #temp_plate = temperature_module.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    tube_rack = ctx.load_labware("opentrons_24_tuberack_nest_1.5ml_snapcap", "8")

    tip_rack_20 = ctx.load_labware("opentrons_96_filtertiprack_20ul","9")
    #mag_module = ctx.load_module("magnetic module", "10")
    #mag_plate = mag_module.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    tip_rack_300 = ctx.load_labware("opentrons_96_tiprack_300ul","11")

    p20s = ctx.load_instrument("p20_single_gen2", "left", tip_racks=[tip_rack_20])
    p300s = ctx.load_instrument("p300_single_gen2", "right", tip_racks=[tip_rack_300])

    for pipette in [p20s, p300s]:
        pipette.pick_up_tip()
#[pcr96, standard_plate, agar_plate, deep_well, strips, reservoir, temp_plate, tube_rack, mag_plate]
        for labware in [pcr96, standard_plate, agar_plate, deep_well, strips, reservoir, tube_rack]:
            pipette.aspirate(1, labware.wells_by_name()["A1"].bottom())
        pipette.return_tip()
