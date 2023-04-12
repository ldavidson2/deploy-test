import boto3
import io
import json
import smtplib
import os
import stripe
import jwt
import cognitojwt
import time
from botocore.client import Config
from twilio.rest import Client
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from boto3.dynamodb.conditions import Key, Attr
from fastapi import Body, Depends, FastAPI, Request, Form, Response
from typing import List, Annotated
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from datetime import date
from datetime import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

testCondition:'attribute_not_exists(email)'

stripe.api_key = "sk_test_51MjQdBAB1aJ9omUKkgCZWRsSUq6kzLl0OQHGYH9smakMaYl3YcdAmaNm6iwR8y9Gy3LjsU3vMG2XY8mQ0aACLs0t006roSgoOB"
awsAccessKey = "AKIAX3FHVXYSKFFYPGE7"
awsSecretAccessKey = "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"

dynamodb = boto3.resource('dynamodb', region_name="us-east-2",
         aws_access_key_id=awsAccessKey,
         aws_secret_access_key= awsSecretAccessKey)
table = dynamodb.Table('test6-DB-staging')

s3Bucket = boto3.resource(service_name='s3', region_name='us-east-2', 
         aws_access_key_id=awsAccessKey, aws_secret_access_key=awsSecretAccessKey)

s3_client = boto3.client('s3')

bucket = s3Bucket.Bucket('memorexbucket134102-dev')

cognito = boto3.client('cognito-idp')

twilio_sid = 'ACf436585983fcf4df53a1db5fd2246db7'
twilio_auth_token = 'fffd7c4699ab70c339b9bb170437ce01'
twilio = Client(twilio_sid, twilio_auth_token)

myEmail = "hjeffersonriver@gmail.com"
myPassword = "mweqtwxuiftugeyc"


class PatientFile(BaseModel):
    fileName: str | None = None
    patientEmail: str | None = None
    testId: str | None = None

class Payment(BaseModel):
    subId: str | None = None
    id: str | None = None
    email: str | None = None
    name: str | None = None
 
class Test(BaseModel):
    fileName: str | None = None
    patientEmail: str | None = None
    testId: str | None = None
    status: str | None = None
    score: str | None = None
    dateSent: str | None = None
    link: str | None = None

class Patient(BaseModel):
    PK: str | None = None
    SK: str | None = None
    physicianEmail: str | None = None
    oldEmail: str | None = None
    firstName: str | None = None
    lastName: str | None = None
    email: str | None = None
    phoneNumber: str | None = ""
    dateOfBirth: str | None = None
    sex: str | None = None
    dementiaLikelihood: str | None = None
    notes: str | None = ""
    tests: list[Test] | None = None

class Physician(BaseModel):
    PK: str | None = None
    SK: str | None = None
    clinicName: str | None = None
    companyEmail: str | None = None
    companyNumber: str | None = ""
    oldEmail: str | None = None
    email: str | None = None
    firstName: str | None = None
    lastName: str | None = None
    phoneNumber: str | None = ""
    securityLevel: int | None = None
    specialty: str | None = ""

class Admin(BaseModel):
    PK: str | None = None
    SK: str | None = None
    oldEmail: str | None = None
    companyEmail: str | None = None
    clinicName: str | None = None
    companyNumber: str | None = ""
    securityLevel: int | None = None

class Individual(BaseModel):
    PK: str | None = None
    SK: str | None = None
    companyEmail: str | None = None
    companyNumber: str | None = ""
    oldEmail: str | None = None
    email: str | None = None
    securityLevel: int | None = None
    firstName: str | None = None
    lastName: str | None = None
    clinicName: str | None = None
    specialty: str | None = ""

class PatientMessage(BaseModel):
    PK: str
    SK: str
    physicianName: str
    subject: str
    message: str
    sendMethod: str



def verify_user(tokenExp):
    current_time = time.time()
    if (int(current_time) <= int(tokenExp)):
        return True
    else:
        return False



@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    with open('static/index.html') as f:
        html = f.read()
    return HTMLResponse(content=html, status_code=200)

@app.get("/{index}", response_class=HTMLResponse)
async def index(request: Request):
    with open('static/index.html') as f:
        html = f.read()
    return HTMLResponse(content=html, status_code=200)

@app.get("/user/{email}")
async def get_user(email, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])


    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel < 3):
        response = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )

        return response

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json")  

@app.get("/{PK}/{PID}/{SK}/{SID}")
async def get_specific(PK, PID, SK, SID, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel < 3):
        response = table.get_item(
            Key={
                'PK': PK + '#' + PID,
                'SK': SK + '#' + SID
            }
        )
        return response

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 

@app.get("/checkEmail/{email}")
async def check_email(email):
    emailResults = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(email.lower())
    )

    if len(emailResults["Items"]) == 0:
        response = '{"message": "Used email is unique", "success": "true"}'

    else:
        response = '{"message": "Used email already exists", "success": "false"}'

    return Response(content=response, media_type="application/json")

    response = '{"message": "Invalid credentials", "success": "false"}'
    return   Response(content=response, media_type="application/json") 
    
@app.get("/checkUpdatedEmail/{currentEmail}/{newEmail}")
async def check_email(currentEmail, newEmail, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel < 3):
        newEmailResults = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(newEmail.lower())
        )

        myEmailResults = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(currentEmail.lower())
        )

        if len(newEmailResults["Items"]) == 0:
            response = '{"message": "Used email is unique", "success": "true"}'
            
        elif len(newEmailResults["Items"]) > 0:
            otherSK = newEmailResults['Items'][0]['SK']
            mySK = myEmailResults['Items'][0]['SK']
            if mySK == otherSK:
                response = '{"message": "Used email is unique", "success": "true"}'
                return Response(content=response, media_type="application/json")

            else: 
                response = '{"message": "Used email already exists", "success": "false"}'
                return Response(content=response, media_type="application/json")

        else:
            response = '{"message": "Used email already exists", "success": "false"}'

        return Response(content=response, media_type="application/json")

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 
    

@app.post("/newAdmin")
async def new_admin(admin: Admin):
    adminResults = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(admin.companyEmail.lower())
    )

    if len(adminResults["Items"]) == 0:
        table.put_item(
            Item={
                'PK': admin.PK,
                'SK': admin.SK,
                'companyEmail': admin.companyEmail,
                'clinicName': admin.clinicName,
                'companyNumber': admin.companyNumber,
                'securityLevel': admin.securityLevel,
                'email': admin.companyEmail,
                'phoneNumber': admin.companyNumber
            },
        )
        response = '{"message": "Used email is unique", "success": "true"}'
        return Response(content=response, media_type="application/json")
    else:
        response = '{"message": "Used email already exists", "success": "false"}'
        return Response(content=response, media_type="application/json")
    
@app.post("/updateAdmin")
async def update_admin(admin: Admin):
    myCompany = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(admin.oldEmail.lower())
    )
    adminUpdate = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(admin.companyEmail.lower())
    )

    PK = myCompany['Items'][0]['PK']
    SK = myCompany['Items'][0]['SK']

    physicians = table.scan(
        FilterExpression=Attr('PK').eq(PK) & Attr('SK').contains("USER")
    )

    for i in range(len(physicians['Items'])):
        physicianPK = physicians["Items"][i]['PK']
        physicianSK = physicians["Items"][i]['SK']
        table.update_item(
        Key={
            'PK': physicianPK,
            'SK': physicianSK
        },
        UpdateExpression='SET companyEmail = :val1, clinicName = :val2, companyNumber = :val3',
        ExpressionAttributeValues={
        ':val1': admin.companyEmail,
        ':val2': admin.clinicName,
        ':val3': admin.companyNumber
        }
    )
    
    if len(adminUpdate["Items"]) == 0:
        table.update_item(
            Key={
                'PK': PK,
                'SK': SK
            },
            UpdateExpression='SET companyEmail = :val1, email = :val2, clinicName = :val3, companyNumber = :val4, phoneNumber = :val5',
            ExpressionAttributeValues={
            ':val1': admin.companyEmail,
            ':val2': admin.companyEmail,
            ':val3': admin.clinicName,
            ':val4': admin.companyNumber,
            ':val5': admin.companyNumber
            }
        )
        response = '{"message": "Used email is unique", "success": "true"}'
        return Response(content=response, media_type="application/json")

    
    elif len(adminUpdate["Items"]) > 0:
        otherSK = adminUpdate['Items'][0]['SK']
        if SK == otherSK:
            table.update_item(
                Key={
                    'PK': PK,
                    'SK': SK
                },
                UpdateExpression='SET companyEmail = :val1, email = :val2, clinicName = :val3, companyNumber = :val4, phoneNumber = :val5',
                ExpressionAttributeValues={
                ':val1': admin.companyEmail,
                ':val2': admin.companyEmail,
                ':val3': admin.clinicName,
                ':val4': admin.companyNumber,
                ':val5': admin.companyNumber
                }
            )
            response = '{"message": "Used email is unique", "success": "true"}'
            return Response(content=response, media_type="application/json")

        else: 
            response = '{"message": "Used email already exists", "success": "false"}'
            return Response(content=response, media_type="application/json")

    else:
        response = '{"message": "Used email already exists", "success": "false"}'
        return Response(content=response, media_type="application/json")
    
@app.get("/deleteCustomer/{email}")
async def delete_customer(email, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel < 2):
        currentCustomer = stripe.Customer.search(
            query="email:'%s'" % (email)
        )
        stripe.Customer.delete(
            "%s" % (currentCustomer.data[0].id)
        )
    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 

@app.post("/deleteAdmin")
async def delete_physician(admin: Admin):
    admin = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(admin.companyEmail)
    )

    PK = admin['Items'][0]['PK']
    SK = admin['Items'][0]['SK']

    table.delete_item(
        Key={
            'PK': PK,
            'SK': SK
        }
    )

    physicians = table.scan(
        FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("USER")
    )

    for i in range(len(physicians['Items'])):
        physicianPK = physicians["Items"][i]['PK']
        physicianSK = physicians["Items"][i]['SK']

        patients = table.scan(
            FilterExpression=Attr('PK').eq(physicianSK) & Attr('SK').contains("PATI")
        )
        
        for i in range(len(patients["Items"])):
            patientPK = patients["Items"][i]['PK']
            patientSK = patients["Items"][i]['SK']
            table.delete_item(
                Key={
                    'PK': patientPK,
                    'SK': patientSK
                }
            )

        physicianUsername = cognito.list_users(
            UserPoolId='us-east-2_tZIGe1Zgs',
            AttributesToGet=[
                'sub',
            ],
            Filter="email='%s'" % (physicians["Items"][i]['email'])
        )
        response = cognito.admin_delete_user(
            UserPoolId='us-east-2_tZIGe1Zgs',
            Username=physicianUsername['Users'][0]['Username']
        )
        table.delete_item(
            Key={
                'PK': physicianPK,
                'SK': physicianSK
            }
        )

    

    # Patient delete test



@app.post("/newIndividual")
async def new_individual(individual: Individual):
    individualResults = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(individual.companyEmail.lower())
    )

    if len(individualResults["Items"]) == 0:
        table.put_item(
            Item={
                'PK': individual.PK,
                'SK': individual.SK,
                'firstName': individual.firstName,
                'lastName': individual.lastName,
                'clinicName': individual.clinicName,
                'specialty': individual.specialty,
                'email': individual.companyEmail,
                'phoneNumber': individual.companyNumber,
                'companyEmail': individual.companyEmail,
                'companyNumber': individual.companyNumber,
                'securityLevel': individual.securityLevel
            }
        )
        response = '{"message": "Used email is unique", "success": "true"}'
        return Response(content=response, media_type="application/json")
    else:
        response = '{"message": "Used email already exists", "success": "false"}'
        return Response(content=response, media_type="application/json")

@app.post("/updateIndividual")
async def update_individual(individual: Individual):
    myIndividual = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(individual.oldEmail.lower())
    )
    individualUpdate = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(individual.companyEmail.lower())
    )

    PK = myIndividual['Items'][0]['PK']
    SK = myIndividual['Items'][0]['SK']

    patients = table.scan(
        FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI")
    )

    for i in range(len(patients['Items'])):
        patientPK = patients["Items"][i]['PK']
        patientSK = patients["Items"][i]['SK']
        table.update_item(
        Key={
            'PK': patientPK,
            'SK': patientSK
        },
        UpdateExpression='SET physicianEmail = :val1',
        ExpressionAttributeValues={
        ':val1': individual.companyEmail
        }
    )

    if len(individualUpdate["Items"]) == 0:
        table.update_item(
            Key={
                'PK': PK,
                'SK': SK
            },
            UpdateExpression='SET firstName = :val1, lastName = :val2, email = :val3, phoneNumber = :val4, specialty = :val5, clinicName = :val6, companyEmail = :val7, companyNumber = :val8',
            ExpressionAttributeValues={
            ':val1': individual.firstName,
            ':val2': individual.lastName,
            ':val3': individual.companyEmail,
            ':val4': individual.companyNumber,
            ':val5': individual.specialty,
            ':val6': individual.clinicName,
            ':val7': individual.companyEmail,
            ':val8': individual.companyNumber
            }
        )
        response = '{"message": "Used email is unique", "success": "true"}'
        return Response(content=response, media_type="application/json")

    elif len(individualUpdate["Items"]) > 0:
        otherSK = individualUpdate['Items'][0]['SK']
        if SK == otherSK:
            table.update_item(
                Key={
                    'PK': PK,
                    'SK': SK
                },
                UpdateExpression='SET firstName = :val1, lastName = :val2, email = :val3, phoneNumber = :val4, specialty = :val5, clinicName = :val6, companyEmail = :val7, companyNumber = :val8',
                ExpressionAttributeValues={
                ':val1': individual.firstName,
                ':val2': individual.lastName,
                ':val3': individual.companyEmail,
                ':val4': individual.companyNumber,
                ':val5': individual.specialty,
                ':val6': individual.clinicName,
                ':val7': individual.companyEmail,
                ':val8': individual.companyNumber
                }         
            )
            response = '{"message": "Used email is unique", "success": "true"}'
            return Response(content=response, media_type="application/json")

        else: 
            response = '{"message": "Used email already exists", "success": "false"}'
            return Response(content=response, media_type="application/json")

    else:
        response = '{"message": "Used email already exists", "success": "false"}'
        return Response(content=response, media_type="application/json")
        
@app.post("/deleteIndividual")
async def delete_physician(individual: Individual):
    individual = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(individual.companyEmail)
    )

    PK = individual['Items'][0]['PK']
    SK = individual['Items'][0]['SK']

    table.delete_item(
        Key={
            'PK': PK,
            'SK': SK
        }
    )

    patients = table.scan(
        FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI")
    )
    # )\docs\api\events

    for i in range(len(patients['Items'])):
        patientPK = patients["Items"][i]['PK']
        patientSK = patients["Items"][i]['SK']
        table.delete_item(
        Key={
            'PK': patientPK,
            'SK': patientSK
        }
    )



@app.post("/newPhysician")
async def new_physician(physician: Physician):
    physicianResults = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(physician.email)
    )

    if len(physicianResults["Items"]) == 0:
        table.put_item(
            Item={
                'PK': physician.PK,
                'SK': physician.SK,
                'clinicName': physician.clinicName,
                'companyEmail': physician.companyEmail,
                'companyNumber': physician.companyNumber,
                'email': physician.email,
                'firstName': physician.firstName,
                'lastName': physician.lastName,
                'phoneNumber': physician.phoneNumber,
                'securityLevel': physician.securityLevel,
                'specialty': physician.specialty
            },
        )
        response = '{"message": "Used email is unique", "success": "true"}'
        return Response(content=response, media_type="application/json")
    else:
        response = '{"message": "Used email already exists", "success": "false"}'
        return Response(content=response, media_type="application/json")
    
@app.post("/updatePhysician")
async def update_physician(physician: Physician):
    myPhysician = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(physician.oldEmail.lower())
    )
    physicianUpdate = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(physician.email.lower())
    )

    PK = myPhysician['Items'][0]['PK']
    SK = myPhysician['Items'][0]['SK']

    patients = table.scan(
        FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI")
    )

    for i in range(len(patients['Items'])):
        patientPK = patients["Items"][i]['PK']
        patientSK = patients["Items"][i]['SK']
        table.update_item(
        Key={
            'PK': patientPK,
            'SK': patientSK
        },
        UpdateExpression='SET physicianEmail = :val1',
        ExpressionAttributeValues={
        ':val1': physician.email
        }
    )

    if len(physicianUpdate["Items"]) == 0:
        table.update_item(
            Key={
                'PK': PK,
                'SK': SK
            },
            UpdateExpression='SET firstName = :val1, lastName = :val2, email = :val3, phoneNumber = :val4, specialty = :val5',
            ExpressionAttributeValues={
            ':val1': physician.firstName,
            ':val2': physician.lastName,
            ':val3': physician.email,
            ':val4': physician.phoneNumber,
            ':val5': physician.specialty
            }
        )
        response = '{"message": "Used email is unique", "success": "true"}'
        return Response(content=response, media_type="application/json")

    elif len(physicianUpdate["Items"]) > 0:
        otherSK = physicianUpdate['Items'][0]['SK']
        if SK == otherSK:
            table.update_item(
                Key={
                    'PK': PK,
                    'SK': SK
                },
                UpdateExpression='SET firstName = :val1, lastName = :val2, email = :val3, phoneNumber = :val4, specialty = :val5',
                ExpressionAttributeValues={
                ':val1': physician.firstName,
                ':val2': physician.lastName,
                ':val3': physician.email,
                ':val4': physician.phoneNumber,
                ':val5': physician.specialty
                }
            )
            response = '{"message": "Used email is unique", "success": "true"}'
            return Response(content=response, media_type="application/json")

        else: 
            response = '{"message": "Used email already exists", "success": "false"}'
            return Response(content=response, media_type="application/json")

    else:
        response = '{"message": "Used email already exists", "success": "false"}'
        return Response(content=response, media_type="application/json")

    
@app.get("/physicians/{email}")
async def get_physicians(email, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel == 0):
        company = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )

        PK = company['Items'][0]['PK']

        response = table.scan(
            FilterExpression=Attr('PK').eq(PK) & Attr('SK').contains("USER")
        )

        return response

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 

@app.post("/deletePhysician")
async def delete_physician(physician: Physician):
    physician = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(physician.email)
    )

    PK = physician['Items'][0]['PK']
    SK = physician['Items'][0]['SK']

    table.delete_item(
        Key={
            'PK': PK,
            'SK': SK
        }
    )

    patients = table.scan(
        FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI")
    )

    for i in range(len(patients['Items'])):
        patientPK = patients["Items"][i]['PK']
        patientSK = patients["Items"][i]['SK']
        table.delete_item(
        Key={
            'PK': patientPK,
            'SK': patientSK
        }
    )

@app.post("/lockPhysician")
async def lock_physician(physician: Physician):
    oldSecurityLevel = physician.securityLevel
    newSecurityLevel = 2 if oldSecurityLevel == 3 else 3
    physician = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(physician.email)
    )

    PK = physician['Items'][0]['PK']
    SK = physician['Items'][0]['SK']

    table.update_item(
        Key={
            'PK': PK,
            'SK': SK
        },
        UpdateExpression='SET securityLevel = :val1',
        ExpressionAttributeValues={
        ':val1': newSecurityLevel
        }
    )



@app.post("/newPatient")
async def new_patient(patient: Patient):
    patientResults = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(patient.email)
    )

    if len(patientResults["Items"]) == 0:
        table.put_item(
            Item={
                'PK': patient.PK,
                'SK': patient.SK,
                'physicianEmail': patient.physicianEmail,
                'firstName': patient.firstName,
                'lastName': patient.lastName,
                'email': patient.email, 
                'phoneNumber': patient.phoneNumber,
                'dateOfBirth': patient.dateOfBirth,
                'sex': patient.sex,
                'dementiaLikelihood': patient.dementiaLikelihood,
                'notes': patient.notes,
                'tests': []
            },
        )
        response = '{"message": "Used email is unique", "success": "true"}'
        return Response(content=response, media_type="application/json")
    else:
        response = '{"message": "Used email already exists", "success": "false"}'
        return Response(content=response, media_type="application/json")

@app.post("/updatePatient")
async def update_patient(patient: Patient):
    myPatient = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(patient.oldEmail.lower())
    )
    patientUpdate = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(patient.email.lower())
    )

    PK = myPatient['Items'][0]['PK']
    SK = myPatient['Items'][0]['SK']

    if len(patientUpdate["Items"]) == 0:
        table.update_item(
            Key={
                'PK': PK,
                'SK': SK
            },
            UpdateExpression ='Set firstName = :val1, lastName = :val2, email = :val3, phoneNumber = :val4, dateOfBirth = :val5, sex = :val6, dementiaLikelihood = :val7, notes = :val8',
            ExpressionAttributeValues={
            ':val1': patient.firstName,
            ':val2': patient.lastName,
            ':val3': patient.email,
            ':val4': patient.phoneNumber,
            ':val5': patient.dateOfBirth,
            ':val6': patient.sex,
            ':val7': patient.dementiaLikelihood,
            ':val8': patient.notes
            }
        )
        response = '{"message": "Used email is unique", "success": "true"}'
        return Response(content=response, media_type="application/json")

    elif len(patientUpdate["Items"]) > 0:
        otherSK = patientUpdate['Items'][0]['SK']
        if SK == otherSK:
            table.update_item(
                Key={
                    'PK': PK,
                    'SK': SK
                },
                UpdateExpression ='Set firstName = :val1, lastName = :val2, email = :val3, phoneNumber = :val4, dateOfBirth = :val5, sex = :val6, dementiaLikelihood = :val7, notes = :val8',
                ExpressionAttributeValues={
                ':val1': patient.firstName,
                ':val2': patient.lastName,
                ':val3': patient.email,
                ':val4': patient.phoneNumber,
                ':val5': patient.dateOfBirth,
                ':val6': patient.sex,
                ':val7': patient.dementiaLikelihood,
                ':val8': patient.notes
                }
            )
            response = '{"message": "Used email is unique", "success": "true"}'
            return Response(content=response, media_type="application/json")

        else: 
            response = '{"message": "Used email already exists", "success": "false"}'
            return Response(content=response, media_type="application/json")

    else:
        response = '{"message": "Used email already exists", "success": "false"}'
        return Response(content=response, media_type="application/json")
        


@app.get("/patients/{email}")
async def get_patients(email, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and (securityLevel == 1 or securityLevel == 2)):
        physician = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )

        SK = physician['Items'][0]['SK']

        patients = table.scan(
            FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI")
        )
        
        return patients

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 

@app.get("/searchPhysicians/{email}/{search}")
async def get_physicians(email, search, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel == 0):
        company = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )

        PK = company['Items'][0]['PK']
        physicians = table.scan(
            FilterExpression=Attr('PK').eq(PK) & Attr('SK').contains("USER")
        )

        searchResults = []

        for i in range(len(physicians['Items'])):
            fullName = physicians["Items"][i]['firstName'].lower() + " " + physicians["Items"][i]['lastName'].lower()
            if (fullName in search.lower()) or (search.lower() in fullName) or (search.lower() in physicians["Items"][i]['email'].lower()) or (physicians["Items"][i]['email'].lower() in search.lower()):
                searchResults.append(physicians["Items"][i])
            # if search != "":
            #     physician = table.scan(
            #         FilterExpression=Attr('PK').eq(PK) & Attr('SK').contains("USER") & (Attr('firstName').contains(search) | Attr('lastName').contains(search) | Attr('specialty').contains(search) | Attr('email').contains(search.lower()))
            #     )
            #     print(physician)
            #     searchResults = physician["Items"]
            
            # elif search == "":
            #     physician = table.scan(
            #     FilterExpression=Attr('PK').eq(PK) & Attr('SK').contains("USER")
            #     )

        return searchResults

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 
    
@app.get("/searchPatients/{email}/{search}")
async def get_patients(email, search, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel == 1 or securityLevel == 2):
        physician = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )

        SK = physician['Items'][0]['SK']
        patients = table.scan(
            FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI")
        )

        searchResults = []
        
        for i in range(len(patients['Items'])):
            fullName = patients["Items"][i]['firstName'].lower() + " " + patients["Items"][i]['lastName'].lower()
            if (fullName in search.lower()) or (search.lower() in fullName):
                searchResults.append(patients["Items"][i])

        # if search != "":
        #     patients = table.scan(
        #     FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI") & (Attr('firstName').contains(search.lower()) | Attr('firstName').contains(search) | Attr('lastName').contains(search.upper()) | Attr('lastName').contains(search.upper()) | Attr('email').contains(search.lower()))
        #     )
        # elif search == "":
        #     patients = table.scan(
        #     FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI")
        # )
        
        return searchResults

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 
  

@app.get("/filteredPatients/{email}/{dementiaLikelihood}/{sex}/{ageMin}/{ageMax}")
async def get_patients(email, dementiaLikelihood, sex, ageMin, ageMax, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel == 1 or securityLevel == 2):
        today = date.today()
        physician = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )

        SK = physician['Items'][0]['SK']

        if sex == "empty" and ageMax == "empty" and dementiaLikelihood != "empty":
            patients = table.scan(
                FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI") & Attr('dementiaLikelihood').eq(dementiaLikelihood)
            )

            filteredPatients = []

            for i in range(len(patients['Items'])):
                patientDateOfBirth = patients["Items"][i]['dateOfBirth']
                born = datetime.strptime(patientDateOfBirth, '%Y-%m-%d').date()
                patientAge = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                if (int(ageMin) <= patientAge):
                    filteredPatients.append(patients["Items"][i])

        elif sex == "empty" and ageMax != "empty" and dementiaLikelihood != "empty":
            patients = table.scan(
                FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI") & Attr('dementiaLikelihood').eq(dementiaLikelihood)
            )

            filteredPatients = []

            for i in range(len(patients['Items'])):
                patientDateOfBirth = patients["Items"][i]['dateOfBirth']
                born = datetime.strptime(patientDateOfBirth, '%Y-%m-%d').date()
                patientAge = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                if (int(ageMin) <= patientAge <= int(ageMax)):
                    filteredPatients.append(patients["Items"][i])

        elif sex == "empty" and ageMax != "empty" and dementiaLikelihood == "empty":
            patients = table.scan(
                FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI")
            )

            filteredPatients = []

            for i in range(len(patients['Items'])):
                patientDateOfBirth = patients["Items"][i]['dateOfBirth']
                born = datetime.strptime(patientDateOfBirth, '%Y-%m-%d').date()
                patientAge = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                if (int(ageMin) <= patientAge <= int(ageMax)):
                    filteredPatients.append(patients["Items"][i])

        elif ageMax == "empty" and sex != "empty" and dementiaLikelihood != "empty":
            patients = table.scan(
                FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI") & Attr('dementiaLikelihood').eq(dementiaLikelihood) & Attr('sex').eq(sex)
            )

            filteredPatients = []

            for i in range(len(patients['Items'])):
                patientDateOfBirth = patients["Items"][i]['dateOfBirth']
                born = datetime.strptime(patientDateOfBirth, '%Y-%m-%d').date()
                patientAge = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                if (int(ageMin) <= patientAge):
                    filteredPatients.append(patients["Items"][i])

        elif ageMax == "empty" and sex != "empty" and dementiaLikelihood == "empty":
            patients = table.scan(
                FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI") & Attr('sex').eq(sex)
            )

            filteredPatients = []

            for i in range(len(patients['Items'])):
                patientDateOfBirth = patients["Items"][i]['dateOfBirth']
                born = datetime.strptime(patientDateOfBirth, '%Y-%m-%d').date()
                patientAge = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                if (int(ageMin) <= patientAge):
                    filteredPatients.append(patients["Items"][i])

        elif dementiaLikelihood == "empty" and sex != "empty" and ageMax != "empty":
            patients = table.scan(
                FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI") & Attr('sex').eq(sex)
            )

            filteredPatients = []

            for i in range(len(patients['Items'])):
                patientDateOfBirth = patients["Items"][i]['dateOfBirth']
                born = datetime.strptime(patientDateOfBirth, '%Y-%m-%d').date()
                patientAge = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                if (int(ageMin) <= patientAge <= int(ageMax)):
                    filteredPatients.append(patients["Items"][i])
        
        else:
            patients = table.scan(
                FilterExpression=Attr('PK').eq(SK) & Attr('SK').contains("PATI") & Attr('dementiaLikelihood').eq(dementiaLikelihood)
            )

            filteredPatients = []

            for i in range(len(patients['Items'])):
                patientDateOfBirth = patients["Items"][i]['dateOfBirth']
                born = datetime.strptime(patientDateOfBirth, '%Y-%m-%d').date()
                patientAge = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                if (int(ageMin) <= patientAge <= int(ageMax)):
                    filteredPatients.append(patients["Items"][i])
        
        return filteredPatients

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 

@app.post("/deletePatient")
async def delete_patient(patient: Patient):
    patient = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(patient.email)
    )

    PK = patient['Items'][0]['PK']
    SK = patient['Items'][0]['SK']

    table.delete_item(
        Key={
            'PK': PK,
            'SK': SK
        }
    )

@app.post("/sendPatientLinkEmail")
async def send_patient_email(patientMessage: PatientMessage):
    print(patientMessage.subject)
    print(patientMessage.message)
    print("email")

    response = table.get_item(
        Key={
            'PK': patientMessage.PK,
            'SK': patientMessage.SK
        }
    )

    toEmail = response["Item"]["email"]

    message = MIMEMultipart()
    message['Subject'] = patientMessage.subject
    message['From'] = myEmail
    message['To'] = toEmail
    content = MIMEText(patientMessage.message, 'plain')

    message.attach(content)

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(myEmail, myPassword)
    server.sendmail(myEmail, toEmail, message.as_string())
    server.close()

    # currentTests = response['Item']['tests']

    # if currentTests == []:
    #     allTests = [{'result': 'none', 'testId': patientMessage.testId, 'status': 'incomplete', 'dateSent': datetime.today().strftime('%Y-%m-%d')}]
    # else:
    #     allTests = currentTests + [{'result': 'none', 'testId': patientMessage.testId, 'status': 'incomplete', 'dateSent': datetime.today().strftime('%Y-%m-%d')}]

    # table.update_item(
    #     Key={
    #         'PK' : patientMessage.PK,
    #         'SK' : patientMessage.SK
    #     },
    #     UpdateExpression ='Set tests = :val1',
    #     ExpressionAttributeValues={
    #         ':val1': allTests
    #     }
    # )

@app.post("/sendPatientLinkText")
async def send_patient_text(patientMessage: PatientMessage):
    print(patientMessage.subject)
    print(patientMessage.message)
    print("text")
    response = table.get_item(
        Key={
            'PK': patientMessage.PK,
            'SK': patientMessage.SK
        }
    )

    message = twilio.messages.create(
                     body=patientMessage.message,
                     from_='+15076876479',
                     to=response['Item']['phoneNumber']
                 )

    # toNumber = response["Item"]["phoneNumber"] + '@pcs.rogers.com'

    # message = MIMEMultipart()
    # content = MIMEText(patientMessage.message, 'plain')

    # message.attach(content)



    # server = smtplib.SMTP('smtp.gmail.com', 587)
    # server.starttls()
    # server.login(myEmail, myPassword)

    # server.sendmail(myEmail, toNumber, message.as_string())
    # server.quit()

    # print(patientMessage.message)

    #UUID = Elijah
    #  E.G = Elijah Gayot... or Evil Guy?
    # H.L = Hyunseung Lee... or Hevil Lguy?
    # It all makes sense now
@app.post("/uploadTestResult/testId/{testId}")
async def upload_test(test: Test):
    fileName = 'PATI#01GWQGK1ABR87S90Y9G255ASAQ-01GWSC605KG33012FFBGJ8K6P5'
    s3Bucket.Bucket('memorexbucket134102-dev').upload_file(Filename=test.fileName, Key=fileName)

# @app.get("/getTestResults/{file}")
# async def get_test(file):
#     fileName = "PATI#" + file
#     response = s3_client.generate_presigned_url('get_object',
#                                                     Params={'Bucket': 'memorexbucket134102-dev',
#                                                             'Key': fileName},
#                                                     ExpiresIn=600)

#     return response

@app.post("/testResults")
async def get_test():
    print("yay")
    



@app.post("/payment")
async def process_payment(payment: Payment):
    print(payment.name)
    try:

        newCustomer = stripe.Customer.create(
            payment_method=payment.id,
            email=payment.email,
            invoice_settings={"default_payment_method": payment.id},
            name=payment.name
        )
        if(payment.subId == '1'):
            stripe.Subscription.create(
                customer=newCustomer,
                items=[{"price": "price_1MtB2YAB1aJ9omUKvqVzgOUo"}],
                metadata={"customer": newCustomer.id}
            )
        elif(payment.subId == '2'):
            stripe.Subscription.create(
                customer=newCustomer,
                items=[{"price": "price_1MtB75AB1aJ9omUKdt0ReJ2q"}],
                metadata={"customer": newCustomer.id}
            )
        elif(payment.subId == '3'):
            stripe.Subscription.create(
                customer=newCustomer,
                items=[{"price": "price_1MtB7QAB1aJ9omUKehQkMT0U"}],
                metadata={"customer": newCustomer.id}
            )
            

        response = '{"message": "Payment successful", "success": "true"}'
        return Response(content=response, media_type="application/json")
    except: 
        response = '{"message": "Payment failed", "success": "false"}'
        return Response(content=response, media_type="application/json")
        
@app.get("/showPayment/{email}")
async def get_payment(email, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel < 2):
        currentCustomer = stripe.Customer.search(
            query="email:'%s'" % (email)
        )
        card = stripe.PaymentMethod.list(
            customer="%s" % (currentCustomer.data[0].id),
            type="card"
        )
        # myCard = stripe.Customer.retrieve_source(
        #     "%s" % currentCustomer.data[0].id,
        #     "pm_1Mo8EbAB1aJ9omUKCtmzZtWD"
        # )
        return card

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 

@app.get("/showCustomer/{email}")
async def get_customer(email, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel < 2):
        currentCustomer = stripe.Customer.search(
            query="email:'%s'" % (email)
        )
        
        return currentCustomer

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 

@app.post("/addPaymentMethod")
async def add_payment(payment: Payment):
    currentCustomer = stripe.Customer.search(
        query="email: '%s'" % (payment.email)
    )

    stripe.PaymentMethod.attach(
        "%s" % (payment.id),
        customer = "%s" % (currentCustomer.data[0].id)
    )

    stripe.Customer.modify(
        "%s" % (currentCustomer.data[0].id),
        invoice_settings={"default_payment_method": "%s" % (payment.id)},
    )

@app.get("/setDefaultCard/{email}/{paymentId}") # needs token verification.. don't forget LEO
async def set_default(email, paymentId):

    currentCustomer = stripe.Customer.search(
        query="email: '%s'" % (email)
    )

    stripe.Customer.modify(
        "%s" % (currentCustomer.data[0].id),
        invoice_settings={"default_payment_method": "%s" % (paymentId)},
    )


@app.get("/deletePaymentMethod/{cardId}")
async def delete_payment(cardId, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel < 2):
        deleteCard=stripe.PaymentMethod.detach(
            "%s" % (cardId)
        )
        return deleteCard

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 

# @app.post("/updatePayment/{email}") #incomplete and not in use currently
# async def update_payment(payment:Payment):
#     stripe.Customer.modify(
#             payment_method=payment.id,
#             email=payment.email,
#             invoice_settings={"default_payment_method": payment.id},
#             name=payment.name
#         )

#     currentCustomer = stripe.Customer.retrieve()
#     stripe.Subscription.modify(
#             customer=currentCustomer,
#             items=[{"price": newPrice}]
#         )

@app.get("/subscription/{email}")
async def get_subscription(email, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid):
        user = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )

        companyEmail = user['Items'][0]['companyEmail']
        myQuery = "email:'%s'" % (companyEmail)
        my_customer = stripe.Customer.search(query=myQuery)

        if my_customer.data == []:
            return(True)

        else: 
            return(my_customer.data[0].delinquent)

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 

@app.get("/updateSubscription/{email}/{subId}")
async def update_subscription(email, subId, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel < 2):

        currentCustomer = stripe.Customer.search(
            query="email:'%s'" % (email)
        )
        currentSubscription = stripe.Subscription.search(
            query = "metadata['customer']:'%s'" % (currentCustomer.data[0].id)
        )
        currentSubItem = stripe.SubscriptionItem.list(
            subscription= "%s" % (currentSubscription.data[0].id)
        )
        if(subId == '1'):
            stripe.Subscription.modify(
                "%s" % (currentSubscription.data[0].id),
                items=[{"id":  "%s" % (currentSubItem.data[0].id), "price": "price_1MtB2YAB1aJ9omUKvqVzgOUo"}]
            )
        elif(subId == '2'):
            stripe.Subscription.modify(
                "%s" % (currentSubscription.data[0].id),
                items=[{"id": currentSubItem.data[0].id, "price": "price_1MtB75AB1aJ9omUKdt0ReJ2q"}]
            )
        elif(subId == '3'):
            stripe.Subscription.modify(
                "%s" % (currentSubscription.data[0].id),
                items=[{"id": currentSubItem.data[0].id, "price": "price_1MtB7QAB1aJ9omUKehQkMT0U"}]
            )
        return currentSubItem.data[0]

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 

@app.get("/deleteSubscription/{email}")
async def delete_subscription(email, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel < 2):
        currentCustomer = stripe.Customer.search(
                query="email:'%s'" % (email)
            )
        currentSubscription = stripe.Subscription.search(
            query = "metadata['customer']:'%s'" % (currentCustomer.data[0].id)
        )
        stripe.Subscription.modify(
            "%s" % (currentSubscription.data[0].id),
            cancel_at_period_end="true",
        )
        return currentSubscription
        #?????????????????

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 

@app.get("/currentSubscription/{email}/{buttonType}")
async def get_subscription(email,buttonType, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel < 3):
        currentCustomer = stripe.Customer.search(
                query="email:'%s'" % (email)
            )
        currentSubscription = stripe.Subscription.search(
            query = "metadata['customer']:'%s'" % (currentCustomer.data[0].id)
        )
        if buttonType == "Cancel":
            stripe.Subscription.modify(
            "%s" % (currentSubscription.data[0].id),
            cancel_at_period_end="true",
        )
        elif buttonType == "Resume":
            stripe.Subscription.modify(
            "%s" % (currentSubscription.data[0].id),
            cancel_at_period_end="false",
        )


        return currentSubscription

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 

@app.get("/currentProduct/{email}")
async def current_product(email, idToken):
    myToken: dict = cognitojwt.decode(
        idToken,
        'us-east-2',
        'us-east-2_tZIGe1Zgs',
        app_client_id='3jtm0l02mte04uhs0m1hqmfg7k'
    )

    response = cognito.get_user(
        AccessToken=idToken
    )

    for i in range(len(response['UserAttributes'])):
        if response['UserAttributes'][i]['Name'] == 'custom:securityLevel':
            securityLevel = int(response['UserAttributes'][i]['Value'])

    token_is_valid = verify_user(myToken['exp'])
    if (token_is_valid and securityLevel < 2):

        currentCustomer = stripe.Customer.search(
                    query="email:'%s'" % (email)
                )
        currentSubscription = stripe.Subscription.search(
            query = "metadata['customer']:'%s'" % (currentCustomer.data[0].id)
        )
            
        currentSubItem = stripe.SubscriptionItem.list(
            subscription= "%s" % (currentSubscription.data[0].id)
        )
        currentProduct = stripe.Product.retrieve(
            "%s" % (currentSubItem.data[0].price.product)
        )

    else:
        response = '{"message": "Invalid credentials", "success": "false"}'
        return   Response(content=response, media_type="application/json") 
 
    return currentProduct