from fastapi import FastAPI
import math
from pydantic import BaseModel
from typing import List
import asyncio
import opentrons.execute as oe
import opentrons.simulate as os
import opentronsfastapi

# Set our opentrons_env to opentrons.simulate
# On real robots, this would be set to opentrons.execute
opentronsfastapi.opentrons_env = oe

app = FastAPI()

class DispenseWell(BaseModel):
    address: str

@app.post("/api/demo")
@opentronsfastapi.opentrons_execute()
def demo_procedure(dispenseWell:DispenseWell):

    # Asyncio must be set to allow the robot to run protocols in
    # the background while still responding to API requests
    asyncio.set_event_loop(asyncio.new_event_loop())
    ctx = opentronsfastapi.opentrons_env.get_protocol_api('2.9')

    ctx.home()
    plate = ctx.load_labware("corning_96_wellplate_360ul_flat", 1)
    tip_rack = ctx.load_labware("opentrons_96_filtertiprack_20ul", 2)
    p20 = ctx.load_instrument("p20_single_gen2", "left", tip_racks=[tip_rack])

    p20.pick_up_tip()

    p20.aspirate(10, plate.wells_by_name()['A1'])
    p20.dispense(10, plate.wells_by_name()[dispenseWell.address])

    p20.drop_tip()


##################### Build time #######################

class AssemblyWell(BaseModel):
    name: str
    address: str
    uuid: str

class AssemblyPlate(BaseModel):
    tuberack: bool
    position: int
    wells: List[AssemblyWell]
    name: str
    uuid: str

class AssemblyTransfer(BaseModel):
    toAddress: str
    fromPosition: int
    fromAddress: str
    volume: float
    water: float

class AssemblyDirections(BaseModel):
    assemblyPlates: List[AssemblyPlate]
    assemblyTransfers: List[AssemblyTransfer]
    maxVol: float

@app.post("/api/build")
@opentronsfastapi.opentrons_execute()
def build_func(directions: AssemblyDirections):
    asyncio.set_event_loop(asyncio.new_event_loop())
    ctx = opentronsfastapi.opentrons_env.get_protocol_api('2.9')

    # Setup labwares
    plate_dict = {}
    build = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "1")
    plate_dict[1] = build
    positions = []
    for plate in directions.assemblyPlates:
        positions.append(plate.position)
        if plate.tuberack == True:
            plate_dict[plate.position] = ctx.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", str(plate.position))
        if plate.tuberack == False:
            plate_dict[plate.position] = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", str(plate.position))
    maxPos = max(positions)

    # Setup tips
    boxes_required = math.ceil(len(directions.assemblyTransfers)/96)
    tip_racks = []
    for _ in range(0, boxes_required):
        maxPos+=1
        tip_racks.append(ctx.load_labware("opentrons_96_filtertiprack_20ul", str(maxPos)))

    # Setup pipette
    p20s = ctx.load_instrument("p20_single_gen2", "left", tip_racks=tip_racks)

    # Run transfers
    ctx.home()
    for transfer in directions.assemblyTransfers:
        p20s.pick_up_tip()
        if transfer.water > 0.25:
            p20s.aspirate(transfer.water, plate_dict[2].wells_by_name()["A1"])
            p20s.aspirate(transfer.volume, plate_dict[transfer.fromPosition].wells_by_name()[transfer.fromAddress])
            p20s.dispense(transfer.volume + transfer.water, plate_dict[1].wells_by_name()[transfer.toAddress])
            p20s.blow_out()
        else:
            p20s.aspirate(transfer.volume, plate_dict[transfer.fromPosition].wells_by_name()[transfer.fromAddress])
            p20s.dispense(transfer.volume, plate_dict[1].wells_by_name()[transfer.toAddress])
            p20s.blow_out()
        p20s.mix(1, 4)
        p20s.drop_tip()

@app.post("/api/transformation_prep/{quantity}")
@opentronsfastapi.opentrons_execute()
def transform_prep(quantity: int):
    asyncio.set_event_loop(asyncio.new_event_loop())
    ctx = opentronsfastapi.opentrons_env.get_protocol_api('2.9')
    ctx.home()
    comp_plate = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "1")
    comp = ctx.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", "2").wells_by_name()["A1"]
    p300s = ctx.load_instrument("p300_single_gen2", "right", tip_racks=[ctx.load_labware("opentrons_96_filtertiprack_200ul", "3")])
    p300s.distribute(15, comp, comp_plate.wells()[:quantity])
    ctx.home()

@app.post("/api/transformation/{quantity}")
@opentronsfastapi.opentrons_execute()
def transform(quantity: int):
    asyncio.set_event_loop(asyncio.new_event_loop())
    ctx = opentronsfastapi.opentrons_env.get_protocol_api('2.9')
    comp_cells = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "1")
    build = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "2")
    p20m = ctx.load_instrument("p20_multi_gen2", "left", tip_racks=[ctx.load_labware("opentrons_96_filtertiprack_20ul", "3")])
    water = ctx.load_labware("nest_1_reservoir_195ml", "5").wells_by_name()["A1"]

    lanes = math.ceil(quantity/8)
    for i in range(0, lanes):
        p20m.pick_up_tip()
        p20m.transfer(6, water, build.rows()[0][i], mix_after=(3,3), new_tip='never')
        p20m.transfer(1, build.rows()[0][i], comp_cells.rows()[0][i], new_tip='never')
        p20m.drop_tip()
    ctx.home()

@app.post("/api/plate/{quantity}")
@opentronsfastapi.opentrons_execute()
def plate(quantity: int):
    asyncio.set_event_loop(asyncio.new_event_loop())
    ctx = opentronsfastapi.opentrons_env.get_protocol_api('2.9')
    ctx.home()
    comp_cells = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "1")
    lb = ctx.load_labware("nest_1_reservoir_195ml", "2").wells_by_name()["A1"]
    
    plate_num = int(quantity/24)
    leftover_lanes = quantity%24
    if leftover_lanes > 0:
        plate_num+=1

    agar_plates = [ctx.load_labware("biorad_96_wellplate_200ul_pcr", str(x)) for x in range(3,3+plate_num)]
    tip_racks = [ctx.load_labware("opentrons_96_filtertiprack_20ul", str(x)) for x in range(7,7+plate_num)]
    p20m = ctx.load_instrument("p20_multi_gen2", "left", tip_racks=tip_racks)

    lanes = math.ceil(quantity/8)

    current_plate = 0
    current_lane = 0
    for lane in range(0,lanes):
        for i in range(0, 4):
            # New lane
            p20m.pick_up_tip()
            if i != 0:
                p20m.transfer(7.5, lb, comp_cells.rows()[0][lane], mix_after=(2,5), new_tip='never')
            p20m.aspirate(7.5, comp_cells.rows()[0][lane])

            # Plate
            p20m.move_to(agar_plates[current_plate].rows()[0][current_lane].top(4))
            p20m.dispense(6.5)
            p20m.move_to(agar_plates[current_plate].rows()[0][current_lane].bottom())
            p20m.move_to(agar_plates[current_plate].rows()[0][current_lane].top())
            p20m.drop_tip()

            # Iterate lanes
            current_lane += 1
            if current_lane == 12:
                current_plate+=1
                current_lane=0
    ctx.home()
