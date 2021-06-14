metadata = {"apiLevel": "2.5"}

def run(ctx):
    build = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "1")
    tubes = ctx.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", "2")
    p20s = ctx.load_instrument("p20_single_gen2", "left", tip_racks=[ctx.load_labware("opentrons_96_filtertiprack_20ul", "3")])

    well_num = 48
    max_vol = 2

    p20s.distribute(10-max_vol, tubes.wells_by_name()["A1"], build.wells()[0:well_num])
