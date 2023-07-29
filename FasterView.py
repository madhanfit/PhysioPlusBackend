from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import StreamingResponse
from pymongo import MongoClient
from typing import List, Optional
import json

Key_Mongo_Cloud = "mongodb://aioverflow:12345@ac-pu6wews-shard-00-00.me4dkct.mongodb.net:27017,ac-pu6wews-shard-00-01.me4dkct.mongodb.net:27017,ac-pu6wews-shard-00-02.me4dkct.mongodb.net:27017/?ssl=true&replicaSet=atlas-jcoztp-shard-0&authSource=admin&retryWrites=true&w=majority"
Key_Mongo_Local = "mongodb://localhost:27017/"

app = FastAPI()
client = MongoClient(Key_Mongo_Cloud)
PatientData = client['Test']['Test']

# Utility function to remove _id field from documents
def remove_id(documents: List[dict]) -> List[dict]:
    return [{**doc, "_id": None} for doc in documents]

# Background job to process the data and generate the JSON response
def process_patients(background_response: BackgroundTasks):
    Find = PatientData.find({})
    Find = list(Find) if Find != None else []
    if len(list(Find)) == 0:
        return None

    Result = list(Find)
    Result = remove_id(Result)

    for i in Result:
        LastAsses = i.get('Assessment', [])
        Checker = len(LastAsses)
        if Checker == 0:
            i['LastAssessment'] = 'No Assessment'
            i['Status'] = "Not Yet"
        else:
            i['LastAssessment'] = LastAsses[-1]
            SeniorDoctorPrescription = i['LastAssessment'].get('SeniorDoctorPrescription', {})
            TreatmentPrescription = SeniorDoctorPrescription.get('TreatmentPrescription', {})
            if TreatmentPrescription != {}:
                i['Status'] = "Completed"
            else:
                i['Status'] = "Partial"

    return Result

# Helper function to generate streaming JSON response
async def stream_generator(background_response: BackgroundTasks):
    patients = await background_response()
    yield "["
    first = True
    for patient in patients:
        if not first:
            yield ","
        yield json.dumps(patient)
        first = False
    yield "]"

# Endpoint for retrieving paginated patients
@app.get("/allPatients/", response_model=List[dict])
async def all_patients(
    skip: int = 0,
    limit: int = 10
):
    background_response = BackgroundTasks()
    background_response.add_task(process_patients, background_response)

    return StreamingResponse(
        stream_generator(background_response),
        media_type="application/json"
    )

# Additional endpoints can be added here for filtering or specific patient retrieval
