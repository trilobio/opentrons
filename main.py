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
        else:
            p20s.aspirate(transfer.volume, plate_dict[transfer.fromPosition].wells_by_name()[transfer.fromAddress])
            p20s.dispense(transfer.volume, plate_dict[1].wells_by_name()[transfer.toAddress])
        p20s.mix(1, 4)
        p20s.drop_tip()

    # Complete and unlock
    if simulate == False:
        unlock()

@app.post("/api/build/newbuild/")
def build(directions: AssemblyDirections):
    # Acquire lock
    lock = get_lock("Test homing")
    if lock == False:
        return {"Message": "App currently locked"}

    # Simulate protocol
    try:
        build_func(os, directions, simulate=True)
    except Exception as e:
        print(e)
        return {"Message": str(e)}

    # Execute protocol
    threading.Thread(target=build_func, args=(opentrons,directions)).start()
    return {"Message": "Lock acquired until build completes"}


