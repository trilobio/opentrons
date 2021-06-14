metadata = {"apiLevel": "2.9"}

def run(ctx):
    p20m = ctx.load_instrument("p20_multi_gen2", "left", tip_racks=[ctx.load_labware("opentrons_96_filtertiprack_20ul","3")])
    ctx.home()
    p20m.pick_up_tip()
    p20m.drop_tip()
    p20m.pick_up_tip()
    p20m.drop_tip()
