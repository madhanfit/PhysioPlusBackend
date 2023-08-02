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



@app.get("/allPatients")
async def allPatients():
    Find = PatientData.find({})
    if Find == None:
        return {"Status" : "Patient Not Found"}
    else:
        Result = list(Find)
        for i in Result:
            del i['_id']
        for i in Result:
            LastAsses = i['Assessment']
            Checker = len(LastAsses)
            if Checker == 0:
                i['LastAssessment'] = 'No Assessment'
                i['Status'] = "Not Yet"
            else:
                i['LastAssessment'] = LastAsses[len(LastAsses) - 1]
                if "TreatmentPrescription" in i['LastAssessment']['SeniorDoctorPrescription']:
                    if i['LastAssessment']['SeniorDoctorPrescription']['TreatmentPrescription'] != dict():
                        i['Status'] = "Completed"
                    else:
                        i['Status'] = "Partial"
                else:
                    i['Status'] = "Not Yet"
        return {"allPatients" : Result}