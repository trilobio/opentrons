metadata = {"apiLevel": "2.9"}

def run(ctx):
    p300s = ctx.load_instrument("p300_single_gen2", "right", tip_racks=[ctx.load_labware("opentrons_96_filtertiprack_200ul", "1")])
    water = ctx.load_labware("nest_1_reservoir_195ml", "2").wells_by_name()["A1"]
    tuberacks = [ctx.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", x) for x in ["3","6"]]
    for tuberack in tuberacks:
        for well in tuberack.wells():
            p300s.transfer(103, water, well, mix_after=(6,50))
