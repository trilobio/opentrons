"""
Drop single channel tip if there's a tip that's still attached 
Ensure that deck slot 9 is empty since we will "ghost" pick up there
"""
metadata = {"apiLevel": "2.9"}

def run(ctx):
    tip_rack = ctx.load_labware("opentrons_96_filtertiprack_20ul","9")
    p20s = ctx.load_instrument("p20_single_gen2", "left", tip_racks=[tip_rack])
    p20s.pick_up_tip()
    p20s.drop_tip()
