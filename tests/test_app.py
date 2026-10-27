import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
import app as hms

c = hms.app.test_client()

def test_health():
    assert c.get("/health").get_json()["status"] == "ok"

def test_full_flow():
    c.post("/patients", data={"name": "Ravi", "age": 30, "gender": "Male"})
    c.post("/doctors", data={"name": "Dr. Rao", "specialization": "Cardiology", "fee": 500})
    r = c.post("/appointments", data={"patient_id": 1, "doctor_id": 1, "date": "2026-11-01", "time": "10:00"}, follow_redirects=True)
    assert b"Appointment booked" in r.data
    r = c.post("/appointments", data={"patient_id": 1, "doctor_id": 1, "date": "2026-11-01", "time": "10:00"}, follow_redirects=True)
    assert b"already has an appointment" in r.data
    c.post("/billing", data={"patient_id": 1, "description": "Consult", "amount": 500})
    assert c.get("/api/stats").get_json()["unpaid"] == 500
    c.post("/billing/1/pay")
    assert c.get("/api/stats").get_json()["revenue"] == 500

def test_pages_render():
    for p in ["/", "/patients", "/doctors", "/appointments", "/billing"]:
        assert c.get(p).status_code == 200

def test_api():
    assert c.post("/api/patients", json={}).status_code == 400
    assert c.post("/api/patients", json={"name": "Sita"}).status_code == 201
    assert any(p["name"] == "Sita" for p in c.get("/api/patients").get_json())
