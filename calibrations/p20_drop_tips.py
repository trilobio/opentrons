metadata = {"apiLevel": "2.9"}

def run(ctx):
    tip_rack = ctx.load_labware("opentrons_96_filtertiprack_20ul","9")
    p20s = ctx.load_instrument("p20_single_gen2", "left", tip_racks=[tip_rack])
    p20m = ctx.load_instrument("p20_multi_gen2", "right", tip_racks=[tip_rack])
    ctx.home()
    p20m.pick_up_tip()
    p20m.drop_tip()
    p20s.pick_up_tip()
    p20s.drop_tip()
