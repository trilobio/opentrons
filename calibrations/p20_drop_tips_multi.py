"""
Drop multi channel tips if there are tips still attached
Ensure that deck slot 9 is empty since we will "ghost" pick up there
"""
metadata = {"apiLevel": "2.9"}

def run(ctx):
    tip_rack = ctx.load_labware("opentrons_96_filtertiprack_20ul","9")
    p20m = ctx.load_instrument("p20_multi_gen2", "right", tip_racks=[tip_rack])
    p20m.pick_up_tip()
    p20m.drop_tip()
