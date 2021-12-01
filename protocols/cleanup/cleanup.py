metadata = {"apiLevel": "2.0"}

bead_ratio = 1.8
sample_volume = 45
elution_volume = 20
sample_cols = 4

# Docs:
# https://s3.amazonaws.com/opentrons-protocol-library-website/Technical+Notes/Nucleic+Acid+Purification+with+Magnetic+Module+OT2+Technical+Note.pdf
def run(protocol):
    # Make sure you are using the right pipette tips
    p300m = protocol.load_instrument("p300_multi_gen2", "right", tip_racks=[protocol.load_labware("opentrons_96_tiprack_300ul", i) for i in [5,6]])

    magnetic_module = protocol.load_module("magnetic module", 1)
    magnetic_module.disengage()
    mag = magnetic_module.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    reagents = protocol.load_labware("nest_12_reservoir_15ml", 2)
    output = protocol.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", 3)

    mag_beads = reagents.wells_by_name()["A1"]
    ethanol = reagents.wells_by_name()["A2"]
    elution_buffer = reagents.wells_by_name()["A3"]
    waste = reagents.wells_by_name()["A12"]

    bead_volume = sample_volume * bead_ratio
    total_volume = bead_volume + sample_volume + 5
    
    # Add beads
    p300m.transfer(bead_volume, mag_beads, mag.columns()[:sample_cols], mix_before=(5, 200), mix_after=(10, bead_volume/2), new_tip='always')

    # Incubate for 5min, engage, and then wait for bead settle for 2min
    protocol.delay(300)
    magnetic_module.engage()
    protocol.delay(120)

    # Switch to slower aspirate and dispense. These numbers are directly what opentrons uses for this protocol.
    p300m.flow_rate.aspirate = 25
    p300m.flow_rate.dispense = 150
    
    # Discard supernatant and wash
    p300m.transfer(total_volume, mag.columns()[:sample_cols], waste, blow_out=True)
    for _ in range(0,2):
        p300m.transfer(180, ethanol, mag.columns()[:sample_cols], air_gap=20)
        protocol.delay(60)
        p300m.transfer(180, mag.columns()[:sample_cols], waste, air_gap=20)

    # Dry for 5min and disengage
    protocol.delay(300)
    magnetic_module.disengage()

    # Add elution buffer, let mix, and then output
    p300m.transfer(elution_volume, elution_buffer, mag.columns()[:sample_cols], mix_after=(10, elution_volume/2))
    protocol.delay(300)
    magnetic_module.engage()
    protocol.delay(120)
    p300m.transfer(elution_volume, mag.columns()[:sample_cols], output.columns()[:sample_cols], blow_out=True)

