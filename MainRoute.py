 
import re
import math
from collections import Counter
from urllib import request
import pandas as pd
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder
from pymongo.mongo_client import MongoClient
import joblib
from fastapi import Response, BackgroundTasks
import random as rd
import datetime
from loguru import logger
import reportgenerator

from datetime import date

Key_Mongo_Cloud = "mongodb://aioverflow:12345@ac-pu6wews-shard-00-00.me4dkct.mongodb.net:27017,ac-pu6wews-shard-00-01.me4dkct.mongodb.net:27017,ac-pu6wews-shard-00-02.me4dkct.mongodb.net:27017/?ssl=true&replicaSet=atlas-jcoztp-shard-0&authSource=admin&retryWrites=true&w=majority"
Key_Mongo_Local = "mongodb://localhost:27017/"

Data = MongoClient(Key_Mongo_Cloud)
PatientData = Data['Test']['Test']
LoginDatabase = Data['Test']['LoginCred']
ReviewData = Data['Test']['Reviews']
ReHab = Data['Test']['Re-Hab']


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

def process_dictionary(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list) and all(isinstance(item, dict) and "value" in item and "label" in item for item in value):
                data[key] = [item["value"] for item in value]
            else:
                process_dictionary(value)
    elif isinstance(data, list):
        for i in range(len(data)):
            process_dictionary(data[i])

# --------------------------- Login Routes -----------------------------------

@app.post("/loginCheck")
async def loginCheck(info : Request):
    
    req_info = await info.json()
    req_info = dict(req_info)
    logger.info("recieved login info")

    Result = (LoginDatabase.find_one(req_info))


    if Result != None:
        Result = dict(Result)
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

    



# -------------------- Receptionist Routes ------- ###################### 

@app.post("/newPatient")
async def NewPatient(info : Request):

    req_info = await info.json()
    req_info = dict(req_info)
    logger.info("recieved new patient details")

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
    
    
    ReturnObj = dict(CurrentData)    
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
    logger.info("recieved basic assesment")

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})


    if Find == None:
        return {"Status" : "Patient Not Found"}
    else:
        Result = dict(Find)
        # print(Result)


        # --- MakesConditionWorse Pre-Processing ------- #
        
        MakesConditionWorse = [i['value'] for i in req_info['Assessment']['MakesConditionWorse']]
        # print(MakesConditionWorse)
        req_info['Assessment']['MakesConditionWorse'] = MakesConditionWorse

        MakesConditionBetter = [i['value'] for i in req_info['Assessment']['MakesConditionBetter']]
        # print(MakesConditionBetter)
        req_info['Assessment']['MakesConditionBetter'] = MakesConditionBetter

        MedicalInformation = [i['value'] for i in req_info['Assessment']['MedicalInformation']]
        # print(MedicalInformation)
        req_info['Assessment']['MedicalInformation'] = MedicalInformation

        MedicalIntervention = [i['value'] for i in req_info['Assessment']['MedicalIntervention']]
        # print(MedicalIntervention)
        req_info['Assessment']['MedicalIntervention'] = MedicalIntervention

        UpdateDict = req_info['Assessment']
        UpdateDict["SeniorDoctorPrescription"] = dict()
        UpdateDict["JuniorDoctorPrescription"] = dict({"DayWise" : []})
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

    # print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found"}
    else:
        Result = dict(Find)
        del Result['_id']
        # process_dictionary(Result)
        return Result

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
    

@app.post("/updatePatient")
async def updatePatient(info : Request):

    # print(await info.body())
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
        



@app.post("/GetDischargeSummary")
async def GetDischargeSummary(info : Request):

    # print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    
    return FileResponse("hospital_report.pdf")
    

    


    
@app.post("/patientFeedback")
async def patientFeedback(info : Request):

    # print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    # print(req_info)

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



################ -------------------------- Senior / Junior Doctor Routes --------------------------------- ################

@app.get("/allPatientsTodayCount")
async def allPatientsTodayCount():
    Find = PatientData.find({})
    Results = list(Find)

    DatedPatients = []



    for Data in Results:
        for i in Data['Assessment']:
            if i['Date'] == str(datetime.date.today()) and i['SeniorWrittenPres'] == False:
                # print("Happy")
                del Data['_id']
                Data['LastAssessment'] = i
                DatedPatients.append(Data)
                # print(Data)
                break
    

    return {
        "allPatientsTodayCount" : len(DatedPatients)
    }


@app.get("/allPatientsToday")
async def allPatientsToday():
    Find = PatientData.find({})
    Results = list(Find)

    DatedPatients = []



    for Data in Results:
        for i in Data['Assessment']:
            if i['Date'] == str(datetime.date.today()) and i['SeniorWrittenPres'] == False:
                # print("Happy")
                del Data['_id']
                Data['LastAssessment'] = i
                Data['Status'] = None
                if "TreatmentPrescription" in i['SeniorDoctorPrescription']:
                    if i['SeniorDoctorPrescription']['TreatmentPrescription'] != dict():
                        Data['Status'] = "Completed"
                    else:
                        Data['Status'] = "Partial"
                else:
                    Data['Status'] = "Not Yet"
                DatedPatients.append(Data)
                break
    

    return {
        "allPatientsToday" : DatedPatients
    }

## Adding Assessments;

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
            {"Patient_Id": SearchKey, "Assessment.Date": req_info['DateOfAssessment']},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.ShoulderAssessment": 
                    req_info
                
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
            {"Patient_Id": SearchKey, "Assessment.Date": req_info['DateOfAssessment']},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.KneeAssessment": 
                    req_info
                
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
            {"Patient_Id": SearchKey, "Assessment.Date": req_info['DateOfAssessment']},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.BalanceAssessment": 
                    req_info
                
            }}
        )

        #medKCO,personal,duration,painAss,irritability:

        return {"Status" : "Successful"}  





@app.post("/LowBackAssessment")
async def LowBackAssessment(info : Request):

    # print(await info.body())
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
            {"Patient_Id": SearchKey, "Assessment.Date": req_info['DateOfAssessment']},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.LowBackAssessment": 
                    req_info
                
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
            {"Patient_Id": SearchKey, "Assessment.Date": req_info['DateOfAssessment']},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.PARQPlusAssessment": req_info
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
            {"Patient_Id": SearchKey, "Assessment.Date": req_info['DateOfAssessment']},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.FMSAssessment": 
                    req_info
                
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

        status = PatientData.update_one(
            {"Patient_Id": SearchKey, "Assessment.Date": req_info['DateOfAssessment']},
            {"$set": {
                "Assessment.$.SeniorDoctorPrescription.TreatmentPrescription": req_info
            }}
        )
        print("Status:",status.acknowledged)

        #medKCO,personal,duration,painAss,irritability:

        return {"Status" : "Successful"}

@app.post("/GeneralAssessment")
async def GeneralAssessment(info : Request):

    ## print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    ## print(req_info)

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
        # ## print(req_info)

        Status = PatientData.update_one(
            {"Patient_Id": SearchKey, "Assessment.Date": req_info['DateOfAssessment']},
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

        print(Status)
        print(Status)

        

        #medKCO,personal,duration,painAss,irritability:

        return {"Status" : "Successful"}
    

@app.post("/GetGeneralAssessment")
async def GetGeneralAssessment(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']

    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        Find = dict(Find)
        Assessment = Find['Assessment']
        try:
            for i in Assessment:
                if i['Date'] == req_info['Date']:
                    ResultSend = i['SeniorDoctorPrescription']['GeneralAssessment']
                    return ResultSend
        except:
            return {"Status" : "Not Found"}
     
    

## getting details

@app.post("/GetShoulderAssessment")
async def GetShoulderAssessment(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']

    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        Find = dict(Find)
        Assessment = Find['Assessment']
        for i in Assessment:
            if i['Date'] == req_info['Date']:
                ResultSend = i['SeniorDoctorPrescription']['ShoulderAssessment']
                return ResultSend
    return {"Status" : "Not Found"}



@app.post("/GetKneeAssessment")
async def GetKneeAssessment(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']

    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        Find = dict(Find)
        Assessment = Find['Assessment']
        for i in Assessment:
            if i['Date'] == req_info['Date']:
                ResultSend = i['SeniorDoctorPrescription']['KneeAssessment']
                return ResultSend
    return {"Status" : "Not Found"}
    

@app.post("/GetBalanceAssessment")
async def GetBalanceAssessment(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']

    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        Find = dict(Find)
        Assessment = Find['Assessment']
        for i in Assessment:
            if i['Date'] == req_info['Date']:
                ResultSend = i['SeniorDoctorPrescription']['BalanceAssessment']
                return ResultSend
    return {"Status" : "Not Found"}
    

@app.post("/GetLowBackAssessment")
async def GetLowBackAssessment(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']

    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        Find = dict(Find)
        Assessment = Find['Assessment']
        for i in Assessment:
            if i['Date'] == req_info['Date']:
                ResultSend = i['SeniorDoctorPrescription']['LowBackAssessment']
                return ResultSend
    return {"Status" : "Not Found"}
    

@app.post("/GetPARQPlusAssessment")
async def GetPARQPlusAssessment(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']

    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        Find = dict(Find)
        Assessment = Find['Assessment']
        for i in Assessment:
            if i['Date'] == req_info['Date']:
                ResultSend = i['SeniorDoctorPrescription']['PARQPlusAssessment']
                return ResultSend
    return {"Status" : "Not Found"}
    

@app.post("/GetFMSAssessment")
async def GetFMSAssessment(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']

    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        Find = dict(Find)
        Assessment = Find['Assessment']
        for i in Assessment:
            if i['Date'] == req_info['Date']:
                ResultSend = i['SeniorDoctorPrescription']['FMSAssessment']
                return ResultSend
    return {"Status" : "Not Found"}
    


@app.post("/GetTreatmentPrescription")
async def GetTreatmentPrescription(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']

    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        Find = dict(Find)
        Assessment = Find['Assessment']
        for i in Assessment:
            if i['Date'] == req_info['Date']:
                ResultSend = i['SeniorDoctorPrescription']['TreatmentPrescription']
                return ResultSend
    return {"Status" : "Not Found"}
    

@app.post("/UpdateReview")
async def UpdateReview(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    
    SearchKey = req_info['Patient_Id']
    Find = ReviewData.find({'Patient_Id' : SearchKey})
    Find = list(Find)

    if Find == []:
        return {"Status" : "Review not found"}
    else:
        Find = list(Find)
        for i in Find:
            if i['SeniorDoctorViewed'] == False and i['DateOfReview'] == req_info['DateOfReview']:
                query = {
                    "DateOfReview": req_info['DateOfReview'],
                    "Patient_Id" : req_info['Patient_Id']
                }
                update = {
                    "$set": {
                        "SeniorDoctorViewed": True
                    }
                }
                Status = ReviewData.update_many(query, update)
                if Status.acknowledged == True:
                    return {"Status" : "successful"}
            if i['SeniorDoctorViewed'] == True:
                return {"Status" : "Already updated"}

    return {"Status" : "Couldn't update"}


@app.get("/AllReviews")
async def AllReviews():
    Find = ReviewData.find({})
    Find = list(Find)

    FinalList = []

    for i in Find:
        if i['SeniorDoctorViewed'] == False:
            del i['_id']
            FinalList.append(i)

    return {"AllReviews" : FinalList[::-1]}


@app.get("/ReviewCount")
async def ReviewCount():
    Find = ReviewData.find({})
    Find = list(Find)

    FinalList = []

    for i in Find:
        if i['SeniorDoctorViewed'] == False:
            del i['_id']
            FinalList.append(i)

    return {"ReviewCount" : len(FinalList[::-1])}




@app.post("/ViewReview")
async def ViewReview(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    
    SearchKey = req_info['Patient_Id']
    Find = ReviewData.find_one({'Patient_Id' : SearchKey , "DateOfReview" : req_info['DateOfReview']})

    if Find != None:
        del Find['_id']
        return Find
    else:
        return {"Status" : "Not Found"}






###-------------------- Junior Route --------------------- ######

@app.post("/GetTreatmentTracker")
async def TreatmentTracker(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    
    if Find == None:
        return {"Status" : "Patient Not Found" }
    else:
        ResultDict = {}
        Find = dict(Find)
        ResultDict['Patient_Id'] = Find['Patient_Id']
        ResultDict['Patient_Name'] = Find['Patient_Name']
        ResultDict['Patient_Age'] = Find['Patient_Age']
        ResultDict['Patient_Gender'] = Find['Patient_Gender']
        ResultDict['Patient_Height'] = Find['Patient_Height']
        ResultDict['Patient_Weight'] = Find['Patient_Weight']
        ResultDict['Patient_Contact_No'] = Find['Patient_Contact_No']
    
        ListOfItems = []

        for i in Find['Assessment']:
            CurrDict = {}
            CurrDict['GeneralAssessmentDate'] = i['Date']
            CurrDict['DateWise'] = i['JuniorDoctorPrescription']['DayWise']
            ListOfItems.append(CurrDict)
        
        ResultDict['DailyReview'] = ListOfItems[::-1]

        print(ListOfItems)

        return ResultDict





@app.post("/UpdateTreatmentTracker")
async def TreatmentTracker(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    
    if Find == None:
        return {"Status" : "Patient Not Found" }
    
    updateDayWise = None

    for i in Find['Assessment']:
        if i['Date'] == req_info['GeneralAssessmentDate']:
            updateDayWise = i['JuniorDoctorPrescription']['DayWise']
            break
    
    RecievedDates = [i['Date'] for i in req_info['DateWise']]
    SetOfDates = set(RecievedDates)

    if len(SetOfDates) < len(RecievedDates):
        return {"status" : "duplicates exists"}

    updateDayWise = req_info['DateWise']
    
    Status = PatientData.update_one(
            {"Patient_Id": SearchKey, "Assessment.Date": req_info['GeneralAssessmentDate']},
            {"$set": {
                "Assessment.$.JuniorDoctorPrescription": {
                    "DayWise": updateDayWise
                }
            }}
        )
    
    if Status.acknowledged == True:
        return {"Status" : "Successful"}
    else:
        return {"Status" : "Not Successful"}

    


@app.post("/RaiseReview")
async def RaiseReview(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    
    if Find == None:
        return {"Status" : "Patient Not Found" }
    
    SearchKey = req_info['Patient_Id']
    Find = ReviewData.find({'Patient_Id' : SearchKey})
    Find = list(Find)
    
    for i in Find:
        if i['DateOfReview'] == req_info['DateOfReview']:
            return {"Status" : "Review already exists for this date"}
    

    req_info['SeniorDoctorViewed'] =  False
    
    Check = ReviewData.insert_one(req_info)

    if Check.acknowledged == True:
        return {"Status" : "successful"}
    else:
        return {"Status" :  "not successful"}
    


##################### ------------ All Trainer / Re-Hab Routes ----------------------- ################



@app.post("/trainer/AddPatientBasic")
async def AddPatientBasic(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)


    print(req_info)

    SearchKey = req_info['Patient_Id']
    Find = PatientData.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found" }
    
    ReHabSearch = ReHab.find_one({'Patient_Id' : SearchKey})
    if ReHabSearch != None:
        if ReHabSearch['DateOfAssessment'] == req_info['DateOfAssessment']:
            return {"Status" : "Same date 2 visits"}
    
    req_info['ExerciseSchedule'] = []
    req_info['ExerciseTracking'] = []
    
    Check = ReHab.insert_one(req_info)

    if Check.acknowledged == True:
        return {"Status" : "successful"}
    else:
        return {"Status" :  "not successful"}


@app.post("/trainer/PARQ_Assessment")
async def PARQ_Assessment(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)


    print(req_info)

    SearchKey = req_info['Patient_Id']
    Find = ReHab.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found in Re-Hab" }
    
    myquery = { "Patient_Id": SearchKey }
    del req_info['Patient_Id']
    newvalues = { "$set": { "PARQ_Assessment": req_info } }
    ReHab.update_one(myquery, newvalues)
    return {"Satus" : "Successfully"}
    

    
@app.post("/trainer/AddExerciseSchedule")
async def ExerciseSchedule(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = ReHab.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found in Re-Hab" }
    
    myquery = { "Patient_Id": SearchKey }
    del req_info['Patient_Id']
    newvalues = { "$set": { "ExerciseSchedule": req_info['ExerciseSchedule'] } }
    ReHab.update_one(myquery, newvalues)
    return {"Satus" : "Successfully"}


@app.post("/trainer/ViewExerciseSchedule")
async def ViewExerciseSchedule(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = ReHab.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found in Re-Hab" }
    else:
        Find = dict(Find)
        return Find['ExerciseSchedule']
    

@app.post("/trainer/AddExerciseTracking")
async def ExerciseTracking(info : Request):

    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = ReHab.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found in Re-Hab" }
    
    myquery = { "Patient_Id": SearchKey }
    del req_info['Patient_Id']
    newvalues = { "$set": { "ExerciseTracking": req_info['ExerciseTracking'] } }
    ReHab.update_one(myquery, newvalues)
    return {"Satus" : "Successfully"}


@app.post("/trainer/ViewExerciseTracking")
async def ViewExerciseTracking(info : Request):
    print(await info.body())
    req_info = await info.json()
    req_info = dict(req_info)

    SearchKey = req_info['Patient_Id']
    Find = ReHab.find_one({'Patient_Id' : SearchKey})
    if Find == None:
        return {"Status" : "Patient Not Found in Re-Hab" }
    else:
        Find = dict(Find)
        return Find['ExerciseTracking']
    


