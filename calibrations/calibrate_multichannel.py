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

    p20m = ctx.load_instrument("p20_multi_gen2", "left", tip_racks=[ctx.load_labware("opentrons_96_filtertiprack_20ul","8")])
    p300m = ctx.load_instrument("p300_multi_gen2", "right", tip_racks=[ctx.load_labware("opentrons_96_filtertiprack_200ul","9")])

    for pipette in [p20m]:#, p300m]:
        pipette.pick_up_tip()
        for labware in [pcr96, standard_plate, agar_plate, deep_well, reservoir12, reservoir, temp_plate]:
            pipette.move_to(labware.wells_by_name()["A1"].bottom())
        pipette.return_tip()
