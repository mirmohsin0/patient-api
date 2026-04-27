from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
import json
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Optional

app = FastAPI()


class Patient(BaseModel):
    id: Annotated[str, Field(..., description="ID of the patient", examples=['P01'], max_length=3)]
    name: Annotated[str, Field(..., description="Name of the patient")]
    city: Annotated[str, Field(..., description="City where the patient is living")]
    age: Annotated[int, Field(..., gt=0, description="Age of the patient")]
    gender: Annotated[Literal["male", "female", "others"], Field(..., description="Gender of the patient")]
    height: Annotated[float, Field(..., gt=0, description="Height in meters")]
    weight: Annotated[float, Field(..., gt=0, description="Weight in kgs")]


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    age: Optional[int] = Field(default=None, gt=0)
    gender: Optional[Literal["male", "female", "others"]] = None
    height: Optional[float] = Field(default=None, gt=0)
    weight: Optional[float] = Field(default=None, gt=0)



def fetch_data():
    try:
        with open("patient.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_data(data):
    with open("patient.json", "w") as f:
        json.dump(data, f)


def calculate_bmi_and_verdict(data: dict):
    height = data.get("height")
    weight = data.get("weight")

    if height and weight:
        bmi = round(weight / (height ** 2), 2)

        if bmi < 18.5:
            verdict = "underweight"
        elif bmi < 25:
            verdict = "Normal"
        elif bmi < 30:
            verdict = "Cardiac"
        else:
            verdict = "Obese"

        data["bmi"] = bmi
        data["verdict"] = verdict

    return data



@app.get("/")
def send_request():
    return {"message": "Patient Management System API"}


@app.get("/about")
def about():
    return {"message": "A fully functional API to manage your patient records"}


@app.get("/view")
def view_data():
    data = fetch_data()
    return data


@app.get("/patient/{patient_id}")
def view_patient(
    patient_id: str = Path(..., description="ID of the patient", examples={"example": {"value": "P01"}})
):
    data = fetch_data()

    if patient_id in data:
        return data[patient_id]

    raise HTTPException(status_code=404, detail="Patient not found")


@app.get("/sort")
def sort_patients(
    sort_by: str = Query(..., description="height, weight, bmi"),
    order: str = Query("asc", description="asc or desc")
):
    sort_list = ["height", "weight", "bmi"]

    if sort_by not in sort_list:
        raise HTTPException(status_code=400, detail=f"Invalid field {sort_list}")

    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order")

    data = fetch_data()

    sorted_data = sorted(
        data.values(),
        key=lambda x: x.get(sort_by, 0),
        reverse=(order == "desc")
    )

    return sorted_data


@app.post("/create")
def create_patient(patient: Patient):
    data = fetch_data()

    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient already exists")

    patient_dict = patient.model_dump(exclude={"id"})


    patient_dict = calculate_bmi_and_verdict(patient_dict)

    data[patient.id] = patient_dict
    save_data(data)

    return JSONResponse(
        status_code=201,
        content={"message": "patient created successfully"}
    )


@app.put("/edit/{patient_id}")
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = fetch_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")

    existing = data[patient_id]

    update_data = patient_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        existing[key] = value

    existing = calculate_bmi_and_verdict(existing)

    data[patient_id] = existing
    save_data(data)

    return {
        "message": "Patient updated successfully",
        "data": existing
    }


@app.delete("/delete/{patient_id}")    
def delete_patient(patient_id: str):
    #load data 
    data = fetch_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")

    del data[patient_id]    

    save_data(data)

    return JSONResponse(status_code=200, content={"message":"Patient deleted successfully"})
