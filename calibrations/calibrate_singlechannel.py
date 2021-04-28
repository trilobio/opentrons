metadata = {"apiLevel": "2.9"}

def run(ctx):
    pcr96 = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "1")
    standard_plate = ctx.load_labware("nest_96_wellplate_200ul_flat","2")
    agar_plate = ctx.load_labware("biorad_96_wellplate_200ul_pcr", "3")
    deep_well = ctx.load_labware("nest_96_wellplate_2ml_deep", "4")
    reservoir12 = ctx.load_labware("nest_12_reservoir_15ml", "5")
    reservoir = ctx.load_labware("nest_1_reservoir_195ml", "6")
    tubes = ctx.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", "7")
    standard384 = ctx.load_labware("corning_384_wellplate_112ul_flat", "8")

    p20s = ctx.load_instrument("p20_single_gen2", "left", tip_racks=[ctx.load_labware("opentrons_96_filtertiprack_20ul","10")])
    p300s = ctx.load_instrument("p300_single_gen2", "right", tip_racks=[ctx.load_labware("opentrons_96_filtertiprack_200ul","11")])

    for pipette in [p20s, p300s]:
        pipette.pick_up_tip()
        for labware in [pcr96, standard_plate, agar_plate, deep_well, reservoir12, reservoir, tubes, standard384]:
            pipette.transfer(20, labware.wells_by_name()["A1"].bottom(), labware.wells_by_name()["A1"].bottom(), new_tip='never')
        pipette.return_tip()
