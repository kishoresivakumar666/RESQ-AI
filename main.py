from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sqlite3
import math
import random


# ============================================================
# RESQ AI
# AI-POWERED EMERGENCY RESPONSE CHAIN
# TEAM VORTEX
# ============================================================


app = FastAPI(
    title="RESQ AI",
    description="AI-Powered Emergency Response Chain Monitoring & Failure Prediction System",
    version="1.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# DATABASE
# ============================================================

DATABASE = "resq_ai.db"


def get_connection():
    connection = sqlite3.connect(
        DATABASE,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


def create_database():

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Emergency Cases
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergencies (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id TEXT UNIQUE,

            emergency_type TEXT,

            injured_count INTEGER,

            caller_name TEXT,

            caller_phone TEXT,

            location TEXT,

            latitude REAL,

            longitude REAL,

            distance REAL,

            traffic TEXT,

            risk_score REAL,

            risk_level TEXT,

            ambulance_id TEXT,

            driver_name TEXT,

            driver_status TEXT,

            hospital_id TEXT,

            hospital_name TEXT,

            hospital_status TEXT,

            eta INTEGER,

            gps_available INTEGER,

            case_status TEXT,

            alert_message TEXT,

            created_at TEXT,

            updated_at TEXT
        )
    """)


    # --------------------------------------------------------
    # Ambulances
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ambulances (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            ambulance_id TEXT UNIQUE,

            driver_name TEXT,

            phone TEXT,

            latitude REAL,

            longitude REAL,

            status TEXT,

            gps_available INTEGER
        )
    """)


    # --------------------------------------------------------
    # Hospitals
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            hospital_id TEXT UNIQUE,

            name TEXT,

            latitude REAL,

            longitude REAL,

            emergency_ready INTEGER,

            icu_available INTEGER,

            ventilator_available INTEGER,

            bed_available INTEGER,

            status TEXT
        )
    """)


    # --------------------------------------------------------
    # Communication
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS communication (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id TEXT,

            sender TEXT,

            receiver TEXT,

            message TEXT,

            created_at TEXT
        )
    """)


    # --------------------------------------------------------
    # Alerts
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            case_id TEXT,

            alert_type TEXT,

            severity TEXT,

            message TEXT,

            acknowledged INTEGER,

            created_at TEXT
        )
    """)


    connection.commit()

    connection.close()


create_database()


# ============================================================
# SAMPLE DATA
# ============================================================

def create_sample_data():

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # Ambulances
    # --------------------------------------------------------

    ambulances = [

        (
            "VTX-AMB-01",
            "Driver 01",
            "9000000001",
            11.0168,
            76.9558,
            "Available",
            1
        ),

        (
            "VTX-AMB-02",
            "Driver 02",
            "9000000002",
            11.0250,
            76.9600,
            "Available",
            1
        ),

        (
            "VTX-AMB-03",
            "Driver 03",
            "9000000003",
            11.0100,
            76.9500,
            "Available",
            1
        )
    ]


    for ambulance in ambulances:

        cursor.execute("""
            INSERT OR IGNORE INTO ambulances
            (
                ambulance_id,
                driver_name,
                phone,
                latitude,
                longitude,
                status,
                gps_available
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ambulance)


    # --------------------------------------------------------
    # Hospitals
    # --------------------------------------------------------

    hospitals = [

        (
            "VTX-HOS-01",
            "City Emergency Hospital",
            11.0168,
            76.9558,
            1,
            5,
            3,
            20,
            "Ready"
        ),

        (
            "VTX-HOS-02",
            "Metro Emergency Care",
            11.0300,
            76.9700,
            1,
            3,
            2,
            15,
            "Ready"
        ),

        (
            "VTX-HOS-03",
            "Central Trauma Hospital",
            11.0000,
            76.9400,
            1,
            7,
            5,
            30,
            "Ready"
        )
    ]


    for hospital in hospitals:

        cursor.execute("""
            INSERT OR IGNORE INTO hospitals
            (
                hospital_id,
                name,
                latitude,
                longitude,
                emergency_ready,
                icu_available,
                ventilator_available,
                bed_available,
                status
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, hospital)


    connection.commit()

    connection.close()


create_sample_data()


# ============================================================
# WEBSOCKET CONNECTIONS
# ============================================================

connections = []


async def broadcast(message):

    disconnected = []

    for websocket in connections:

        try:

            await websocket.send_json(message)

        except:

            disconnected.append(websocket)


    for websocket in disconnected:

        if websocket in connections:

            connections.remove(websocket)


# ============================================================
# REQUEST MODELS
# ============================================================

class EmergencyRequest(BaseModel):

    emergency_type: str

    injured_count: int

    caller_name: Optional[str] = None

    caller_phone: Optional[str] = None

    location: Optional[str] = None

    latitude: Optional[float] = None

    longitude: Optional[float] = None


class DriverAction(BaseModel):

    action: str


class GPSData(BaseModel):

    latitude: float

    longitude: float


class MessageData(BaseModel):

    sender: str

    receiver: str

    message: str


class HospitalData(BaseModel):

    emergency_ready: Optional[bool] = None

    icu_available: Optional[int] = None

    ventilator_available: Optional[int] = None

    bed_available: Optional[int] = None

    status: Optional[str] = None


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    if None in (
        lat1,
        lon1,
        lat2,
        lon2
    ):

        return 0


    earth_radius = 6371


    lat1 = math.radians(lat1)

    lat2 = math.radians(lat2)


    dlat = lat2 - lat1

    dlon = math.radians(
        lon2 - lon1
    )


    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(dlon / 2) ** 2
    )


    c = (
        2 *
        math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )
    )


    return round(
        earth_radius * c,
        2
    )


# ============================================================
# RESQ AI RISK PREDICTION
# ============================================================

def predict_risk(
    emergency_type,
    injured_count,
    distance,
    traffic
):

    score = 0


    emergency_type = (
        emergency_type
        .lower()
        .strip()
    )


    # --------------------------------------------------------
    # Emergency type
    # --------------------------------------------------------

    if "cardiac" in emergency_type:

        score += 45

    elif "heart" in emergency_type:

        score += 45

    elif "stroke" in emergency_type:

        score += 45

    elif "breathing" in emergency_type:

        score += 40

    elif "critical" in emergency_type:

        score += 45

    elif "accident" in emergency_type:

        score += 35

    elif "fire" in emergency_type:

        score += 35

    else:

        score += 20


    # --------------------------------------------------------
    # Injured people
    # --------------------------------------------------------

    if injured_count >= 5:

        score += 25

    elif injured_count >= 3:

        score += 18

    elif injured_count >= 2:

        score += 12

    else:

        score += 5


    # --------------------------------------------------------
    # Distance
    # --------------------------------------------------------

    if distance > 20:

        score += 20

    elif distance > 10:

        score += 15

    elif distance > 5:

        score += 8


    # --------------------------------------------------------
    # Traffic
    # --------------------------------------------------------

    if traffic == "Heavy":

        score += 15

    elif traffic == "Moderate":

        score += 8

    else:

        score += 2


    score = min(
        score,
        100
    )


    if score >= 70:

        level = "HIGH"

    elif score >= 40:

        level = "MEDIUM"

    else:

        level = "LOW"


    return score, level


# ============================================================
# ETA
# ============================================================

def calculate_eta(
    distance,
    traffic
):

    if distance <= 0:

        return None


    if traffic == "Heavy":

        speed = 20

    elif traffic == "Moderate":

        speed = 35

    else:

        speed = 50


    eta = (
        distance /
        speed
    ) * 60


    return max(
        1,
        round(eta)
    )


# ============================================================
# GENERATE CASE ID
# ============================================================

def generate_case_id():

    connection = get_connection()

    cursor = connection.cursor()


    date = datetime.now().strftime(
        "%Y%m%d"
    )


    prefix = (
        f"VTX-{date}-"
    )


    cursor.execute("""
        SELECT case_id

        FROM emergencies

        WHERE case_id LIKE ?

        ORDER BY id DESC

        LIMIT 1
    """, (prefix + "%",))


    result = cursor.fetchone()


    if result is None:

        number = 1

    else:

        try:

            number = (
                int(
                    result["case_id"]
                    .split("-")[-1]
                )
                + 1
            )

        except:

            number = 1


    connection.close()


    return (
        f"{prefix}"
        f"{number:03d}"
    )


# ============================================================
# FIND SUITABLE HOSPITAL
# ============================================================

def find_hospital(
    latitude,
    longitude
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM hospitals

        WHERE emergency_ready = 1

        AND status = 'Ready'
    """)


    hospitals = cursor.fetchall()


    connection.close()


    if not hospitals:

        return None


    best = None

    best_score = float("inf")


    for hospital in hospitals:

        distance = calculate_distance(

            latitude,

            longitude,

            hospital["latitude"],

            hospital["longitude"]
        )


        score = distance


        # Hospital capacity consideration

        if hospital["bed_available"] <= 0:

            score += 50


        if hospital["icu_available"] <= 0:

            score += 20


        if hospital["ventilator_available"] <= 0:

            score += 10


        if score < best_score:

            best_score = score

            best = hospital


    return best


# ============================================================
# FIND AVAILABLE AMBULANCE
# ============================================================

def find_nearest_ambulance(
    latitude,
    longitude
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM ambulances

        WHERE status = 'Available'
    """)


    ambulances = cursor.fetchall()


    connection.close()


    if not ambulances:

        return None


    best = None

    shortest_distance = float("inf")


    for ambulance in ambulances:

        distance = calculate_distance(

            latitude,

            longitude,

            ambulance["latitude"],

            ambulance["longitude"]
        )


        if distance < shortest_distance:

            shortest_distance = distance

            best = ambulance


    return best, shortest_distance


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {

        "system": "RESQ AI",

        "team": "Vortex",

        "status": "ONLINE",

        "message":
            "Emergency Response Backend Running"
    }


# ============================================================
# CREATE EMERGENCY
# ============================================================

@app.post(
    "/api/emergencies"
)
async def create_emergency(
    data: EmergencyRequest
):

    case_id = generate_case_id()


    latitude = data.latitude

    longitude = data.longitude


    # --------------------------------------------------------
    # Default location if GPS unavailable
    # --------------------------------------------------------

    if latitude is None:

        latitude = 11.0168


    if longitude is None:

        longitude = 76.9558


    # --------------------------------------------------------
    # Traffic
    # --------------------------------------------------------

    traffic_options = [
        "Normal",
        "Moderate",
        "Heavy"
    ]


    traffic = random.choice(
        traffic_options
    )


    # --------------------------------------------------------
    # Find ambulance for prediction
    # --------------------------------------------------------

    ambulance_result = (
        find_nearest_ambulance(
            latitude,
            longitude
        )
    )


    if ambulance_result:

        ambulance, distance = (
            ambulance_result
        )

    else:

        ambulance = None

        distance = 0


    # --------------------------------------------------------
    # AI risk
    # --------------------------------------------------------

    risk_score, risk_level = (
        predict_risk(

            data.emergency_type,

            data.injured_count,

            distance,

            traffic
        )
    )


    # --------------------------------------------------------
    # Hospital
    # --------------------------------------------------------

    hospital = find_hospital(

        latitude,

        longitude
    )


    if hospital:

        hospital_id = (
            hospital["hospital_id"]
        )

        hospital_name = (
            hospital["name"]
        )

        hospital_status = (
            hospital["status"]
        )

    else:

        hospital_id = None

        hospital_name = (
            "Hospital verification pending"
        )

        hospital_status = (
            "Checking"
        )


    # --------------------------------------------------------
    # ETA
    # --------------------------------------------------------

    eta = calculate_eta(
        distance,
        traffic
    )


    # --------------------------------------------------------
    # Alert
    # --------------------------------------------------------

    if risk_level == "HIGH":

        alert_message = (
            "RESQ AI detected HIGH "
            "response risk."
        )

    elif risk_level == "MEDIUM":

        alert_message = (
            "RESQ AI detected MEDIUM "
            "response risk."
        )

    else:

        alert_message = None


    now = datetime.now().isoformat()


    # --------------------------------------------------------
    # Save emergency
    # --------------------------------------------------------

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        INSERT INTO emergencies
        (
            case_id,
            emergency_type,
            injured_count,
            caller_name,
            caller_phone,
            location,
            latitude,
            longitude,
            distance,
            traffic,
            risk_score,
            risk_level,
            hospital_id,
            hospital_name,
            hospital_status,
            eta,
            gps_available,
            case_status,
            driver_status,
            alert_message,
            created_at,
            updated_at
        )

        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        case_id,

        data.emergency_type,

        data.injured_count,

        data.caller_name,

        data.caller_phone,

        data.location,

        latitude,

        longitude,

        distance,

        traffic,

        risk_score,

        risk_level,

        hospital_id,

        hospital_name,

        hospital_status,

        eta,

        1,

        "Reported",

        "Waiting",

        alert_message,

        now,

        now
    ))


    # --------------------------------------------------------
    # Save alert
    # --------------------------------------------------------

    if risk_level == "HIGH":

        cursor.execute("""
            INSERT INTO alerts
            (
                case_id,
                alert_type,
                severity,
                message,
                acknowledged,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?)
        """, (

            case_id,

            "AI_RISK",

            "HIGH",

            alert_message,

            0,

            now
        ))


    connection.commit()

    connection.close()


    # --------------------------------------------------------
    # Real-time control-room notification
    # --------------------------------------------------------

    await broadcast({

        "event":
            "NEW_EMERGENCY",

        "case_id":
            case_id,

        "emergency_type":
            data.emergency_type,

        "injured_count":
            data.injured_count,

        "risk_level":
            risk_level,

        "risk_score":
            risk_score,

        "hospital":
            hospital_name,

        "eta":
            eta
    })


    return {

        "success": True,

        "case_id": case_id,

        "risk_score": risk_score,

        "risk_level": risk_level,

        "distance": distance,

        "traffic": traffic,

        "hospital": hospital_name,

        "hospital_id": hospital_id,

        "eta": eta,

        "message":
            "Emergency registered successfully"
    }


# ============================================================
# GET ALL EMERGENCIES
# ============================================================

@app.get(
    "/api/emergencies"
)
def get_emergencies():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM emergencies

        ORDER BY id DESC
    """)


    cases = cursor.fetchall()


    connection.close()


    return [
        dict(case)
        for case in cases
    ]


# ============================================================
# GET SINGLE EMERGENCY
# ============================================================

@app.get(
    "/api/emergencies/{case_id}"
)
def get_emergency(
    case_id: str
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM emergencies

        WHERE case_id = ?
    """, (case_id,))


    case = cursor.fetchone()


    connection.close()


    if case is None:

        raise HTTPException(

            status_code=404,

            detail="Case not found"
        )


    return dict(case)


# ============================================================
# ASSIGN AMBULANCE
# ============================================================

@app.post(
    "/api/emergencies/"
    "{case_id}/assign-ambulance"
)
async def assign_ambulance(
    case_id: str
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM emergencies

        WHERE case_id = ?
    """, (case_id,))


    case = cursor.fetchone()


    if case is None:

        connection.close()

        raise HTTPException(

            status_code=404,

            detail="Case not found"
        )


    ambulance_result = (
        find_nearest_ambulance(

            case["latitude"],

            case["longitude"]
        )
    )


    if ambulance_result is None:

        cursor.execute("""
            UPDATE emergencies

            SET
                case_status = ?,
                alert_message = ?,
                updated_at = ?

            WHERE case_id = ?
        """, (

            "Waiting for Ambulance",

            "No ambulance currently available.",

            datetime.now().isoformat(),

            case_id
        ))


        cursor.execute("""
            INSERT INTO alerts
            (
                case_id,
                alert_type,
                severity,
                message,
                acknowledged,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?)
        """, (

            case_id,

            "RESOURCE_SHORTAGE",

            "HIGH",

            "No ambulance currently available.",

            0,

            datetime.now().isoformat()
        ))


        connection.commit()

        connection.close()


        await broadcast({

            "event":
                "AMBULANCE_UNAVAILABLE",

            "case_id":
                case_id
        })


        return {

            "success": False,

            "message":
                "No ambulance available"
        }


    ambulance, distance = (
        ambulance_result
    )


    eta = calculate_eta(

        distance,

        case["traffic"]
    )


    # --------------------------------------------------------
    # Assign
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE ambulances

        SET status = 'Assigned'

        WHERE ambulance_id = ?
    """, (
        ambulance["ambulance_id"],
    ))


    cursor.execute("""
        UPDATE emergencies

        SET

            ambulance_id = ?,

            driver_name = ?,

            driver_status = ?,

            case_status = ?,

            distance = ?,

            eta = ?,

            updated_at = ?

        WHERE case_id = ?
    """, (

        ambulance["ambulance_id"],

        ambulance["driver_name"],

        "Assignment Sent",

        "Waiting for Driver",

        distance,

        eta,

        datetime.now().isoformat(),

        case_id
    ))


    connection.commit()

    connection.close()


    # --------------------------------------------------------
    # Notify driver + control room
    # --------------------------------------------------------

    await broadcast({

        "event":
            "AMBULANCE_ASSIGNED",

        "case_id":
            case_id,

        "ambulance_id":
            ambulance["ambulance_id"],

        "driver":
            ambulance["driver_name"],

        "emergency_type":
            case["emergency_type"],

        "injured_count":
            case["injured_count"],

        "location":
            case["location"],

        "risk_level":
            case["risk_level"],

        "risk_score":
            case["risk_score"],

        "hospital":
            case["hospital_name"],

        "eta":
            eta
    })


    return {

        "success": True,

        "ambulance_id":
            ambulance["ambulance_id"],

        "driver":
            ambulance["driver_name"],

        "distance":
            distance,

        "eta":
            eta,

        "message":
            "Assignment sent to driver"
    }


# ============================================================
# DRIVER ACCEPT / DENY
# ============================================================

@app.post(
    "/api/emergencies/"
    "{case_id}/driver-response"
)
async def driver_response(

    case_id: str,

    data: DriverAction
):

    action = (
        data.action
        .strip()
        .upper()
    )


    if action not in [
        "ACCEPT",
        "DENY"
    ]:

        raise HTTPException(

            status_code=400,

            detail=
                "Only ACCEPT or DENY is allowed"
        )


    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM emergencies

        WHERE case_id = ?
    """, (case_id,))


    case = cursor.fetchone()


    if case is None:

        connection.close()

        raise HTTPException(

            status_code=404,

            detail="Case not found"
        )


    # ========================================================
    # ACCEPT
    # ========================================================

    if action == "ACCEPT":

        cursor.execute("""
            UPDATE emergencies

            SET

                driver_status = ?,

                case_status = ?,

                gps_available = ?,

                updated_at = ?

            WHERE case_id = ?
        """, (

            "Accepted",

            "En Route",

            1,

            datetime.now().isoformat(),

            case_id
        ))


        connection.commit()

        connection.close()


        await broadcast({

            "event":
                "DRIVER_ACCEPTED",

            "case_id":
                case_id,

            "ambulance_id":
                case["ambulance_id"],

            "driver":
                case["driver_name"],

            "status":
                "En Route"
        })


        return {

            "success": True,

            "message":
                "Driver accepted emergency",

            "status":
                "En Route"
        }


    # ========================================================
    # DENY
    # ========================================================

    cursor.execute("""
        UPDATE ambulances

        SET status = 'Available'

        WHERE ambulance_id = ?
    """, (
        case["ambulance_id"],
    ))


    cursor.execute("""
        UPDATE emergencies

        SET

            ambulance_id = NULL,

            driver_name = NULL,

            driver_status = ?,

            case_status = ?,

            updated_at = ?

        WHERE case_id = ?
    """, (

        "Denied",

        "Reassigning",

        datetime.now().isoformat(),

        case_id
    ))


    # Create alert

    cursor.execute("""
        INSERT INTO alerts
        (
            case_id,
            alert_type,
            severity,
            message,
            acknowledged,
            created_at
        )

        VALUES (?, ?, ?, ?, ?, ?)
    """, (

        case_id,

        "DRIVER_DENIED",

        "MEDIUM",

        "Driver denied the emergency assignment.",

        0,

        datetime.now().isoformat()
    ))


    connection.commit()

    connection.close()


    await broadcast({

        "event":
            "DRIVER_DENIED",

        "case_id":
            case_id,

        "message":
            "Driver denied. Finding another ambulance."
    })


    # --------------------------------------------------------
    # Automatically assign another ambulance
    # --------------------------------------------------------

    result = await assign_ambulance(
        case_id
    )


    return {

        "success": True,

        "message":
            "Driver denied. Reassignment started.",

        "reassignment":
            result
    }


# ============================================================
# GPS UPDATE
# ============================================================

@app.post(
    "/api/emergencies/"
    "{case_id}/gps"
)
async def update_gps(

    case_id: str,

    data: GPSData
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM emergencies

        WHERE case_id = ?
    """, (case_id,))


    case = cursor.fetchone()


    if case is None:

        connection.close()

        raise HTTPException(

            status_code=404,

            detail="Case not found"
        )


    # --------------------------------------------------------
    # Update emergency location
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE emergencies

        SET

            latitude = ?,

            longitude = ?,

            gps_available = 1,

            updated_at = ?

        WHERE case_id = ?
    """, (

        data.latitude,

        data.longitude,

        datetime.now().isoformat(),

        case_id
    ))


    # --------------------------------------------------------
    # Update ambulance location
    # --------------------------------------------------------

    if case["ambulance_id"]:

        cursor.execute("""
            UPDATE ambulances

            SET

                latitude = ?,

                longitude = ?,

                gps_available = 1

            WHERE ambulance_id = ?
        """, (

            data.latitude,

            data.longitude,

            case["ambulance_id"]
        ))


    connection.commit()

    connection.close()


    # --------------------------------------------------------
    # Real-time map update
    # --------------------------------------------------------

    await broadcast({

        "event":
            "GPS_UPDATE",

        "case_id":
            case_id,

        "ambulance_id":
            case["ambulance_id"],

        "latitude":
            data.latitude,

        "longitude":
            data.longitude
    })


    return {

        "success": True,

        "latitude":
            data.latitude,

        "longitude":
            data.longitude
    }


# ============================================================
# CALL CONTROL ROOM
# ============================================================

@app.post(
    "/api/emergencies/"
    "{case_id}/call-control-room"
)
async def call_control_room(

    case_id: str
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT case_id

        FROM emergencies

        WHERE case_id = ?
    """, (case_id,))


    case = cursor.fetchone()


    if case is None:

        connection.close()

        raise HTTPException(

            status_code=404,

            detail="Case not found"
        )


    now = datetime.now().isoformat()


    cursor.execute("""
        INSERT INTO communication
        (
            case_id,
            sender,
            receiver,
            message,
            created_at
        )

        VALUES (?, ?, ?, ?, ?)
    """, (

        case_id,

        "Driver",

        "Control Room",

        "Driver requested control room communication.",

        now
    ))


    cursor.execute("""
        INSERT INTO alerts
        (
            case_id,
            alert_type,
            severity,
            message,
            acknowledged,
            created_at
        )

        VALUES (?, ?, ?, ?, ?, ?)
    """, (

        case_id,

        "DRIVER_CALL",

        "MEDIUM",

        "Driver requested control room communication.",

        0,

        now
    ))


    connection.commit()

    connection.close()


    await broadcast({

        "event":
            "DRIVER_CALL",

        "case_id":
            case_id,

        "message":
            "Driver wants to contact control room."
    })


    return {

        "success": True,

        "message":
            "Control room notified"
    }


# ============================================================
# SEND MESSAGE
# ============================================================

@app.post(
    "/api/communications/"
    "{case_id}"
)
async def send_message(

    case_id: str,

    data: MessageData
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT case_id

        FROM emergencies

        WHERE case_id = ?
    """, (case_id,))


    case = cursor.fetchone()


    if case is None:

        connection.close()

        raise HTTPException(

            status_code=404,

            detail="Case not found"
        )


    cursor.execute("""
        INSERT INTO communication
        (
            case_id,
            sender,
            receiver,
            message,
            created_at
        )

        VALUES (?, ?, ?, ?, ?)
    """, (

        case_id,

        data.sender,

        data.receiver,

        data.message,

        datetime.now().isoformat()
    ))


    connection.commit()

    connection.close()


    await broadcast({

        "event":
            "NEW_MESSAGE",

        "case_id":
            case_id,

        "sender":
            data.sender,

        "receiver":
            data.receiver,

        "message":
            data.message
    })


    return {

        "success": True,

        "message":
            "Message sent"
    }


# ============================================================
# GET COMMUNICATION
# ============================================================

@app.get(
    "/api/communications/"
    "{case_id}"
)
def get_messages(

    case_id: str
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM communication

        WHERE case_id = ?

        ORDER BY id ASC
    """, (case_id,))


    messages = cursor.fetchall()


    connection.close()


    return [
        dict(message)
        for message in messages
    ]


# ============================================================
# GET AMBULANCES
# ============================================================

@app.get(
    "/api/ambulances"
)
def get_ambulances():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM ambulances

        ORDER BY id
    """)


    ambulances = cursor.fetchall()


    connection.close()


    return [
        dict(ambulance)
        for ambulance in ambulances
    ]


# ============================================================
# GET AVAILABLE AMBULANCES
# ============================================================

@app.get(
    "/api/ambulances/available"
)
def available_ambulances():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM ambulances

        WHERE status = 'Available'
    """)


    ambulances = cursor.fetchall()


    connection.close()


    return [
        dict(ambulance)
        for ambulance in ambulances
    ]


# ============================================================
# GET HOSPITALS
# ============================================================

@app.get(
    "/api/hospitals"
)
def get_hospitals():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM hospitals

        ORDER BY id
    """)


    hospitals = cursor.fetchall()


    connection.close()


    return [
        dict(hospital)
        for hospital in hospitals
    ]


# ============================================================
# UPDATE HOSPITAL
# ============================================================

@app.put(
    "/api/hospitals/{hospital_id}"
)
async def update_hospital(

    hospital_id: str,

    data: HospitalData
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM hospitals

        WHERE hospital_id = ?
    """, (hospital_id,))


    hospital = cursor.fetchone()


    if hospital is None:

        connection.close()

        raise HTTPException(

            status_code=404,

            detail="Hospital not found"
        )


    values = {

        "emergency_ready":
            hospital["emergency_ready"],

        "icu_available":
            hospital["icu_available"],

        "ventilator_available":
            hospital["ventilator_available"],

        "bed_available":
            hospital["bed_available"],

        "status":
            hospital["status"]
    }


    if data.emergency_ready is not None:

        values["emergency_ready"] = int(
            data.emergency_ready
        )


    if data.icu_available is not None:

        values["icu_available"] = (
            data.icu_available
        )


    if data.ventilator_available is not None:

        values["ventilator_available"] = (
            data.ventilator_available
        )


    if data.bed_available is not None:

        values["bed_available"] = (
            data.bed_available
        )


    if data.status is not None:

        values["status"] = data.status


    cursor.execute("""
        UPDATE hospitals

        SET

            emergency_ready = ?,

            icu_available = ?,

            ventilator_available = ?,

            bed_available = ?,

            status = ?

        WHERE hospital_id = ?
    """, (

        values["emergency_ready"],

        values["icu_available"],

        values["ventilator_available"],

        values["bed_available"],

        values["status"],

        hospital_id
    ))


    connection.commit()

    connection.close()


    await broadcast({

        "event":
            "HOSPITAL_UPDATED",

        "hospital_id":
            hospital_id
    })


    return {

        "success": True,

        "message":
            "Hospital information updated"
    }


# ============================================================
# GET ALERTS
# ============================================================

@app.get(
    "/api/alerts"
)
def get_alerts():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM alerts

        ORDER BY id DESC
    """)


    alerts = cursor.fetchall()


    connection.close()


    return [
        dict(alert)
        for alert in alerts
    ]


# ============================================================
# ACKNOWLEDGE ALERT
# ============================================================

@app.put(
    "/api/alerts/"
    "{alert_id}/acknowledge"
)
async def acknowledge_alert(

    alert_id: int
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        UPDATE alerts

        SET acknowledged = 1

        WHERE id = ?
    """, (alert_id,))


    if cursor.rowcount == 0:

        connection.close()

        raise HTTPException(

            status_code=404,

            detail="Alert not found"
        )


    connection.commit()

    connection.close()


    await broadcast({

        "event":
            "ALERT_ACKNOWLEDGED",

        "alert_id":
            alert_id
    })


    return {

        "success": True,

        "message":
            "Alert acknowledged"
    }


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

@app.get(
    "/api/dashboard"
)
def dashboard():

    connection = get_connection()

    cursor = connection.cursor()


    # Active emergencies

    cursor.execute("""
        SELECT COUNT(*)

        AS count

        FROM emergencies

        WHERE case_status
        NOT IN ('Completed', 'Closed')
    """)

    active = cursor.fetchone()["count"]


    # Available ambulances

    cursor.execute("""
        SELECT COUNT(*)

        AS count

        FROM ambulances

        WHERE status = 'Available'
    """)

    available = cursor.fetchone()["count"]


    # High risk

    cursor.execute("""
        SELECT COUNT(*)

        AS count

        FROM emergencies

        WHERE risk_level = 'HIGH'

        AND case_status
        NOT IN ('Completed', 'Closed')
    """)

    high_risk = cursor.fetchone()["count"]


    # Total

    cursor.execute("""
        SELECT COUNT(*)

        AS count

        FROM emergencies
    """)

    total = cursor.fetchone()["count"]


    # Completed

    cursor.execute("""
        SELECT COUNT(*)

        AS count

        FROM emergencies

        WHERE case_status = 'Completed'
    """)

    completed = cursor.fetchone()["count"]


    connection.close()


    return {

        "active_emergencies":
            active,

        "ambulances_available":
            available,

        "high_risk_cases":
            high_risk,

        "total_cases":
            total,

        "completed_cases":
            completed,

        "average_response_time":
            0
    }


# ============================================================
# COMPLETE CASE
# ============================================================

@app.put(
    "/api/emergencies/"
    "{case_id}/complete"
)
async def complete_case(

    case_id: str
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *

        FROM emergencies

        WHERE case_id = ?
    """, (case_id,))


    case = cursor.fetchone()


    if case is None:

        connection.close()

        raise HTTPException(

            status_code=404,

            detail="Case not found"
        )


    # Make ambulance available

    if case["ambulance_id"]:

        cursor.execute("""
            UPDATE ambulances

            SET status = 'Available'

            WHERE ambulance_id = ?
        """, (
            case["ambulance_id"],
        ))


    cursor.execute("""
        UPDATE emergencies

        SET

            case_status = 'Completed',

            driver_status = 'Completed',

            updated_at = ?

        WHERE case_id = ?
    """, (

        datetime.now().isoformat(),

        case_id
    ))


    connection.commit()

    connection.close()


    await broadcast({

        "event":
            "CASE_COMPLETED",

        "case_id":
            case_id
    })


    return {

        "success": True,

        "message":
            "Emergency case completed"
    }


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket(
    "/ws"
)
async def websocket_endpoint(
    websocket: WebSocket
):

    await websocket.accept()

    connections.append(
        websocket
    )


    try:

        while True:

            await websocket.receive_text()


    except WebSocketDisconnect:

        if websocket in connections:

            connections.remove(
                websocket
            )


    except Exception:

        if websocket in connections:

            connections.remove(
                websocket
            )


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn


    print()
    print("=" * 60)
    print("             RESQ AI")
    print("        TEAM VORTEX")
    print("=" * 60)
    print()
    print("Backend is starting...")
    print()
    print("API:")
    print("http://127.0.0.1:8000")
    print()
    print("API Documentation:")
    print("http://127.0.0.1:8000/docs")
    print()
    print("WebSocket:")
    print("ws://127.0.0.1:8000/ws")
    print()
    print("=" * 60)


    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )