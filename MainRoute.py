 
import re
import math
from collections import Counter
from urllib import request
import pandas as pd
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.encoders import jsonable_encoder
from pymongo.mongo_client import MongoClient
import joblib
import random as rd
import datetime

from datetime import date

Key_Mongo_Cloud = "mongodb://aioverflow:12345@ac-pu6wews-shard-00-00.me4dkct.mongodb.net:27017,ac-pu6wews-shard-00-01.me4dkct.mongodb.net:27017,ac-pu6wews-shard-00-02.me4dkct.mongodb.net:27017/?ssl=true&replicaSet=atlas-jcoztp-shard-0&authSource=admin&retryWrites=true&w=majority"
Key_Mongo_Local = "mongodb://localhost:27017/"

Data = MongoClient(Key_Mongo_Cloud)
PatientData = Data['Test']['Test']
LoginDatabase = Data['Test']['LoginCred']

app = FastAPI()


origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

### ----- General Functions ----------

def Dict_to_List(Dictionary):
    return [i['value'] for i in Dictionary]

# --------------------------- Login Routes -----------------------------------

@app.post("/loginCheck")
async def loginCheck(info : Request):
    
    req_info = await info.json()
    req_info = dict(req_info)
    print(req_info)

    Result = (LoginDatabase.find_one(req_info))

    print(Result)

    if Result != None:
        Result = dict(Result)
        print(Result)
        if req_info['userName'] == Result['userName'] and req_info['password'] == Result['password'] and req_info['userType'] == Result['userType']:
            return {
                "Status" : True
            }
        else:
            return {
                "Status" : False
            }
        
    else:
        return {
            "Status" : False
        }

    



# -------------------- Receptionist Routes -------

@app.post("/newPatient")
async def NewPatient(info : Request):

    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    CurrentData = {
                "Patient_Id" : "23" + "ST" + str(rd.randint(100,1000)),
                "Patient_Name" : req_info["Patient_Name"],
                "Patient_Age" : req_info["Patient_Age"],
                "Patient_Gender" : req_info["Patient_Gender"],
                "Patient_Height" : req_info["Patient_Height"],
                "Patient_Weight" : req_info["Patient_Weight"],
                "Patient_Contact_No" : req_info["Patient_Contact_No"],
                "Employed" : req_info["Employed"],
                "Occupation" : req_info["Occupation"],
                "Address" : req_info["Address"],
                "Assessment" : []
            }
    
    
    print(CurrentData)
    ReturnObj = dict(CurrentData)


    ConnectData = Data['Test']['Test']
    
    Check = PatientData.insert_one(CurrentData)

    if Check.acknowledged == True:
        return ReturnObj
    else:
        return {"Status" :  False}
    

    
@app.post("/addBasicAssessment")
async def addBasicAssessment(info : Request):

    # print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)
    print(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})


    if Find == None:
        return {"Status" : "Patient Not Found"}
    else:
        Result = dict(Find)
        # print(Result)


        # --- MakesConditionWorse Pre-Processing ------- #
        
        MakesConditionWorse = [i['value'] for i in req_info['Assessment']['MakesConditionWorse']]
        print(MakesConditionWorse)
        req_info['Assessment']['MakesConditionWorse'] = MakesConditionWorse

        MakesConditionBetter = [i['value'] for i in req_info['Assessment']['MakesConditionBetter']]
        print(MakesConditionBetter)
        req_info['Assessment']['MakesConditionBetter'] = MakesConditionBetter

        MedicalInformation = [i['value'] for i in req_info['Assessment']['MedicalInformation']]
        print(MedicalInformation)
        req_info['Assessment']['MedicalInformation'] = MedicalInformation

        MedicalIntervention = [i['value'] for i in req_info['Assessment']['MedicalIntervention']]
        print(MedicalIntervention)
        req_info['Assessment']['MedicalIntervention'] = MedicalIntervention

        UpdateDict = req_info['Assessment']
        UpdateDict["SeniorDoctorPrescription"] = dict()
        UpdateDict["JuniorDoctorPrescription"] = dict()
        UpdateDict["TrainerPrescription"] = dict()
        UpdateDict["Feedback"] = {}
        UpdateDict["SeniorWrittenPres"] = False
        UpdateDict["SeniorWrittenAsses"] = False

        # print(UpdateDict)

        Result['Assessment'].append(UpdateDict)
        UpdateAssigment = Result['Assessment']

        # print(UpdateAssigment)

        myquery = { "Patient_Id": SearchKey }
        newvalues = { "$set": { "Assessment": UpdateAssigment } }
        PatientData.update_one(myquery, newvalues)
        return {"Satus" : "Successfully"}
    



@app.post("/viewPatient")
async def viewPatient(info : Request):

    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found"}
    else:
        Result = dict(Find)
        del Result['_id']

        return Result

@app.get("/allPatients")
async def allPatients():
    Find = PatientData.find({})
    print("Hello")
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
            else:
                i['LastAssessment'] = LastAsses[len(LastAsses) - 1]
        return {"allPatients" : Result}
    

@app.post("/updatePatient")
async def updatePatient(info : Request):

    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        Result = dict(Find)
        check = PatientData.update_one({'Patient_Id' : req_info["Patient_Id"]},
                   {"$set": {
                       "Patient_Name": req_info["Patient_Name"],
                       "Patient_Age":  req_info["Patient_Age"],
                       "Patient_Gender" : req_info["Patient_Gender"],
                       "Patient_Height" : req_info["Patient_Height"],
                       "Patient_Weight" : req_info["Patient_Weight"],
                       "Patient_Contact_No" : req_info["Patient_Contact_No"],
                       "Employed" : req_info["Employed"],
                       "Occupation" : req_info["Occupation"],
                       "Address" : req_info["Address"]
                        }
                   }
                )
        
        if check.acknowledged == True:
            return {"Status" : True ,  "Patient_Id" : req_info["Patient_Id"]}
        else:
            return {"Status" : False , "Patient_Id" : req_info["Patient_Id"]}
        


        return Result
    
@app.post("/patientFeedback")
async def patientFeedback(info : Request):

    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    print(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found"}
    else:
        Result = dict(Find)
        AllAsses = Result['Assessment']
        UpdateFeed = None

        idx = 0
        for i in AllAsses:
            if i['Date'] == req_info['Date'] :
                UpdateFeed = i
                break
            idx += 1
        if UpdateFeed == None:
            return {"Status" : "Date of Assessment doesn't exits"}
        else:
            UpdateFeed['Feedback'] = req_info['Feedback']
            AllAsses[idx] = UpdateFeed
            check = PatientData.update_one({'Patient_Id' : req_info["Patient_Id"]},
                   {"$set": {
                       "Assessment": AllAsses,
                        }
                   }
                )
            
            if check.acknowledged == True:
                return {"Status" : True}
            else:
                return {"Status" : False}



################ -------------------------- Senior Doctor Routes --------------------------------- ################

@app.get("/allPatientsToday")
async def allPatientsToday():
    Find = PatientData.find({})
    Results = list(Find)

    DatedPatients = []



    for Data in Results:
        for i in Data['Assessment']:
            if i['Date'] == str(datetime.date.today()) and i['SeniorWrittenPres'] == False:
                print("Happy")
                del Data['_id']
                Data['LastAssessment'] = i
                DatedPatients.append(Data)
                print(Data)
                break
    

    return {
        "allPatientsToday" : DatedPatients
    }


@app.post("/ShoulderAssessment")
async def ShoulderAssessment(info : Request):

    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    print(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        # Update the document in MongoDB:
        del req_info['Patient_Id']

        # ListChanges = ["medKCO","personal","duration","painAss","irritability"]
        # for i in ListChanges:
        #     req_info[i] = Dict_to_List(req_info[i])
        # print(req_info)

        PatientData.update_one(
            {"Patient_Id": SearchKey, "Assessment.Date": str(datetime.date.today())},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.ShoulderAssessment": {
                    "Happy" : "Man"
                }
            }}
        )

        #medKCO,personal,duration,painAss,irritability:

        return {"Status" : "Successful"}

    
    


@app.post("/KneeAssessment")
async def KneeAssessment(info : Request):

    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    print(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        # Update the document in MongoDB:
        del req_info['Patient_Id']

        # ListChanges = ["medKCO","personal","duration","painAss","irritability"]
        # for i in ListChanges:
        #     req_info[i] = Dict_to_List(req_info[i])
        # print(req_info)

        PatientData.update_one(
            {"Patient_Id": SearchKey, "Assessment.Date": str(datetime.date.today())},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.KneeAssessment": {
                    "Happy" : "Man"
                }
            }}
        )

        #medKCO,personal,duration,painAss,irritability:

        return {"Status" : "Successful"}  


@app.post("/BalanceAssessment")
async def BalanceAssessment(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    print(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        # Update the document in MongoDB:
        del req_info['Patient_Id']

        # ListChanges = ["medKCO","personal","duration","painAss","irritability"]
        # for i in ListChanges:
        #     req_info[i] = Dict_to_List(req_info[i])
        # print(req_info)

        PatientData.update_one(
            {"Patient_Id": SearchKey, "Assessment.Date": str(datetime.date.today())},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.BalanceAssessment": {
                    "Happy" : "Man"
                }
            }}
        )

        #medKCO,personal,duration,painAss,irritability:

        return {"Status" : "Successful"}  





@app.post("/LowBackAssessment")
async def BalanceAssessment(info : Request):

    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    print(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        # Update the document in MongoDB:
        del req_info['Patient_Id']

        # ListChanges = ["medKCO","personal","duration","painAss","irritability"]
        # for i in ListChanges:
        #     req_info[i] = Dict_to_List(req_info[i])
        # print(req_info)

        PatientData.update_one(
            {"Patient_Id": SearchKey, "Assessment.Date": str(datetime.date.today())},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.LowBackAssessment": {
                    "Happy" : "Man"
                }
            }}
        )

        #medKCO,personal,duration,painAss,irritability:

        return {"Status" : "Successful"}




@app.post("/PARQPlusAssessment")
async def PARQPlusAssessmen(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    print(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        # Update the document in MongoDB:
        del req_info['Patient_Id']

        # ListChanges = ["medKCO","personal","duration","painAss","irritability"]
        # for i in ListChanges:
        #     req_info[i] = Dict_to_List(req_info[i])
        # print(req_info)

        PatientData.update_one(
            {"Patient_Id": SearchKey, "Assessment.Date": str(datetime.date.today())},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.PARQPlusAssessmen": {
                    "Happy" : "Man"
                }
            }}
        )

        #medKCO,personal,duration,painAss,irritability:

        return {"Status" : "Successful"}




@app.post("/FMSAssessment")
async def FMSAssessment(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    print(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        # Update the document in MongoDB:
        del req_info['Patient_Id']

        # ListChanges = ["medKCO","personal","duration","painAss","irritability"]
        # for i in ListChanges:
        #     req_info[i] = Dict_to_List(req_info[i])
        # print(req_info)

        PatientData.update_one(
            {"Patient_Id": SearchKey, "Assessment.Date": str(datetime.date.today())},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.FMSAssessment": {
                    "Happy" : "Man"
                }
            }}
        )

        #medKCO,personal,duration,painAss,irritability:

        return {"Status" : "Successful"}


@app.post("/TreatmentPrescription")
async def TreatmentPrescription(info : Request):

    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    print(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        # Update the document in MongoDB:
        del req_info['Patient_Id']

        # ListChanges = ["medKCO","personal","duration","painAss","irritability"]
        # for i in ListChanges:
        #     req_info[i] = Dict_to_List(req_info[i])
        # print(req_info)

        PatientData.update_one(
            {"Patient_Id": SearchKey, "Assessment.Date": str(datetime.date.today())},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.TreatmentPrescription": {
                    "Happy" : "Man"
                }
            }}
        )

        #medKCO,personal,duration,painAss,irritability:

        return {"Status" : "Successful"}

@app.post("/GeneralAssessment")
async def GeneralAssessment(info : Request):

    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    print(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        # Update the document in MongoDB:
        del req_info['Patient_Id']

        ListChanges = ["medKCO","personal","duration","painAss","irritability"]
        for i in ListChanges:
            req_info[i] = Dict_to_List(req_info[i])
        print(req_info)

        PatientData.update_one(
            {"Patient_Id": SearchKey, "Assessment.Date": str(datetime.date.today())},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription": {
                    "GeneralAssessment": req_info,
                    "ShoulderAssessment": {},
                    "KneeAssessment": {},
                    "BalanceAssessment": {},
                    "LowBackAssessment": {},
                    "PARQPlusAssessment": {},
                    "FMSAssessment": {},
                    "TreatmentPrescription": {}
                }
            }}
        )

        #medKCO,personal,duration,painAss,irritability:

        return {"Status" : "Successful"}




