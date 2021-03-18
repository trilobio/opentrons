from fastapi import FastAPI
import math
import asyncio
import sqlite3
import time
import threading
import opentrons.execute as oe
import opentrons.simulate as os
from typing import List

from pydantic import BaseModel

# Config
opentrons = os
left = "p20_single_gen2"
right = "p300_single_gen2"


app = FastAPI()

# Setup sqlite3 lock
conn = sqlite3.connect("lock.db")
c = conn.cursor()
table_sql = """
BEGIN;
CREATE TABLE IF NOT EXISTS lock (
    lock_id INT PRIMARY KEY,
    lock_active BOOL NOT NULL DEFAULT false,
    locked_by TEXT NOT NULL DEFAULT ''
);
INSERT INTO lock(lock_id) VALUES (1) ON CONFLICT DO NOTHING;
UPDATE lock SET lock_active = false, locked_by='' WHERE lock_id=1;
COMMIT;
"""
c.executescript(table_sql)
conn.close()

# Robotic locks
def get_lock(locked_by):
    conn = sqlite3.connect("lock.db")
    c_lock = conn.cursor()
    c_lock.execute("SELECT lock_active, locked_by FROM lock WHERE lock_id=1")
    lock_state = c_lock.fetchone()

    if lock_state[0] == False:
        # Acquire the lock
        c_lock.execute("UPDATE lock SET lock_active = true, locked_by=? WHERE lock_id=1", (locked_by,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False # Fail to acquire the lock

def unlock():
    conn = sqlite3.connect("lock.db")
    c_lock = conn.cursor()
    c_lock.execute("UPDATE lock SET lock_active = false, locked_by='' WHERE lock_id=1")
    conn.commit()
    conn.close()

### Test funcs ####

@app.get("/")
def read_root():
    return {"Message": "Hello World"}

@app.get("/test/unlock")
def test_unlock():
    unlock()

def test_lock_func():
    time.sleep(10)
    unlock()
    return {"Message": "Unlocked"}

@app.get("/test/lock")
def test_lock():
    lock = get_lock("Test Lock")
    if lock == False:
        return {"Message": "App currently locked"}
    threading.Thread(target=test_lock_func).start()
    return {"Message": "Lock acquired for 10 seconds"}

def test_home_func():
    asyncio.set_event_loop(asyncio.new_event_loop())
    ctx = opentrons.get_protocol_api('2.9')
    ctx.home()
    unlock()

@app.get("/test/home")
def test_home():
    lock = get_lock("Test homing")
    if lock == False:
        return {"Message": "App currently locked"}
    threading.Thread(target=test_home_func).start()
    return {"Message": "Lock acquired until home completes"}

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


def build_func(ot, directions, simulate=False):
    asyncio.set_event_loop(asyncio.new_event_loop())
    ctx = ot.get_protocol_api('2.9')

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

    # Complete and unlock
    if simulate == False:
        unlock()

@app.post("/api/build/newbuild/")
def build(directions: AssemblyDirections):

    # Simulate protocol
    try:
        build_func(os, directions, simulate=True)
    except Exception as e:
        print(e)
        return {"Message": str(e)}
    
    # Acquire lock
    lock = get_lock("Test homing")
    if lock == False:
        return {"Message": "App currently locked"}

    # Execute protocol
    threading.Thread(target=build_func, args=(opentrons,directions)).start()
    return {"Message": "Lock acquired until build completes"}

#######
def transform_prep_func(ot, quantity, simulate=False):
    asyncio.set_event_loop(asyncio.new_event_loop())
    ctx = ot.get_protocol_api('2.9')
    comp_plate = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "1")
    comp = ctx.load_labware("opentrons_24_tuberack_generic_2ml_screwcap", "2").wells_by_name()["A1"]
    p300s = ctx.load_instrument("p300_single_gen2", "right", tip_racks=[ctx.load_labware("opentrons_96_filtertiprack_200ul", "3")])
    p300s.distribute(15, comp, comp_plate.wells()[:quantity])

    if simulate == False:
        unlock()

@app.get("/api/build/transform_prep/{quantity}")
def transform_prep(quantity: int):
    # Simulate protocol
    try:
        transform_prep_func(os, quantity, simulate=True)
    except Exception as e:
        print(e)
        return {"Message": str(e)}

    # Acquire lock
    lock = get_lock("Test homing")
    if lock == False:
        return {"Message": "App currently locked"}

    threading.Thread(target=transform_prep_func, args=(opentrons,quantity)).start()
    return {"Message": "Lock acquired until build completes"}

#######
def transform_func(ot, quantity, simulate=False):
    asyncio.set_event_loop(asyncio.new_event_loop())
    ctx = ot.get_protocol_api('2.9')
    comp_cells = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "1")
    build = ctx.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", "2")
    p20m = ctx.load_instrument("p20_multi_gen2", "left", tip_racks=[ctx.load_labware("opentrons_96_filtertiprack_20ul", "3")])

    lanes = math.ceil(quantity/8)
    for i in range(0, lanes):
        p20m.transfer(1, build.rows()[0][i], comp_cells.rows()[0][i], new_tip='always')

    if simulate == False:
        unlock()
    
@app.get("/api/build/transform/{quantity}")
def transform(quantity: int):
    # Simulate protocol
    try:
        transform_func(os, quantity, simulate=True)
    except Exception as e:
        print(e)
        return {"Message": str(e)}

    # Acquire lock
    lock = get_lock("Test homing")
    if lock == False:
        return {"Message": "App currently locked"}

    threading.Thread(target=transform_func, args=(opentrons,quantity)).start()
    return {"Message": "Lock acquired until build completes"}

#######
def plate_func(ot, quantity, simulate=False):
    asyncio.set_event_loop(asyncio.new_event_loop())
    ctx = ot.get_protocol_api('2.9')
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

    if simulate == False:
        unlock()

@app.get("/api/build/plate/{quantity}")
def plate(quantity: int):
    # Simulate protocol
    try:
        plate_func(os, quantity, simulate=True)
    except Exception as e:
        print(e)
        return {"Message": str(e)}

    # Acquire lock
    lock = get_lock("Test homing")
    if lock == False:
        return {"Message": "App currently locked"}

    threading.Thread(target=plate_func, args=(opentrons,quantity)).start()
    return {"Message": "Lock acquired until build completes"}

