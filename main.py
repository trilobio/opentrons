from fastapi import FastAPI
import asyncio
import sqlite3
import time
import threading
import opentrons.execute as oe
import opentrons.simulate as os

# Config
opentrons = oe

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
