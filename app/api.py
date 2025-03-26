from fastapi import FastAPI, HTTPException, Header, Query
from typing import Optional, List
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import os
load_dotenv()
app = FastAPI()

# environment variables-------
uri = os.getenv("URI")
API_KEY = os.getenv("API_KEY")

# Database Configurations ---------
db = "NewsletterAI"
col = "articles"
client = MongoClient(uri)
database = client[db]
collection = database[col]


origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://techblog.saeuietpu.in",
    "https://newsletter-ai.saeuietpu.in",
    "https://saeuietpu.in"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class dataReq(BaseModel):
    url: str

class dataStore(BaseModel):
    title: str
    category: str
    date: str
    content: list
    tag: str
class emailParams(BaseModel):
    title: str
    link: str
    des: str
    subs: str

class addFeedback(BaseModel):
    username: str
    email: str
    message: str
class addSub(BaseModel):
    submail: str
def scrape_paragraph_content(url):
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract all text within paragraph (<p>) tags
        paragraphs = soup.find_all('p')
        paragraph_content = "\n".join(p.get_text(strip=True) for p in paragraphs)

        return paragraph_content

    except Exception as e:
        return f"An error occurred: {e}"

# Function to check the API key
def verify_api_key(api_key: str):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Not authorized request")

SMTP_SERVER = "smtpout.secureserver.net"  # GoDaddy Professional Email (Microsoft 365)
SMTP_PORT = 587
PRIMARY_EMAIL = os.getenv("PRIMARY_EMAIL")  # e.g., admin@saeuietpu.in
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Password for admin@saeuietpu.in
ALIAS_EMAIL = "newsletter@saeuietpu.in"


def send_email_with_alias(receiver_email, link, title, des):
    try:
        # Email Content
        subject = "Your Newsletter"
        html_body = f"""
        <html>
            <body>
            <div style="text-align:center; width:100%; display:flex; justify-content:center">
                <div style="width:100%;text-align:center; align-items:center">
                    <h2 style="text-align:center; font-weight:600;">NewsletterAI</h2>
                    <p>An AI generated accurate & informative newsletter</p>
                    <br>
                    <a href={link}><h3>{title}</h3></a>
                    <p>{des}</p>
                    <br>
                    <p style="font-size:12px;color:gray;">If you did not subscribe, please ignore this email.</p>
                </div>
            </div>
            </body>
        </html>
        """

        # Set up the email message
        message = MIMEMultipart()
        message["From"] = ALIAS_EMAIL  # Use the alias email here
        message["To"] = receiver_email
        message["Subject"] = subject

        # Attach the HTML body
        message.attach(MIMEText(html_body, "html"))

        # Connect to the SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(PRIMARY_EMAIL, EMAIL_PASSWORD)  # Authenticate with the primary email
        server.sendmail(ALIAS_EMAIL, receiver_email, message.as_string())

        # Close the connection
        server.quit()

        print(f"Email sent successfully to {receiver_email} from {ALIAS_EMAIL}")
    except Exception as e:
        print(f"Error sending email: {e}")

def send_feedback_mail(receiver_name, message):
    try:
            # Email Content
            subject = "Feedback from SAE"
            html_body = f"""
            <html>
                <body>
                <div style="text-align:center; width:100%; display:flex; justify-content:center">
                    <div style="width:100%;text-align:center; align-items:center">
                        <h2 style="text-align:center; font-weight:600;">SAE UIET PU Feedback</h2>
                        <p></p>
                        <br>
                        <h3>{receiver_name}</h3>
                        <p>{message}</p>
                        <br>
                        <p style="font-size:12px;color:gray;">If you did not subscribe, please ignore this email.</p>
                    </div>
                </div>
                </body>
            </html>
            """

            # Set up the email message
            message = MIMEMultipart()
            message["From"] = ALIAS_EMAIL  # Use the alias email here
            message["To"] = "admin@saeuietpu.in"
            message["Subject"] = subject

            # Attach the HTML body
            message.attach(MIMEText(html_body, "html"))

            # Connect to the SMTP server
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()  # Secure the connection
            server.login(PRIMARY_EMAIL, EMAIL_PASSWORD)  # Authenticate with the primary email
            server.sendmail(ALIAS_EMAIL, "admin@saeuietpu.in", message.as_string())

            # Close the connection
            server.quit()

            print(f"Email sent successfully to {receiver_name} from {ALIAS_EMAIL}")

    except Exception as e:
        print(f"Error sending email: {e}")

# Test the function
# send_email_with_alias("gp43883@gmail.com")

@app.post("/scrapeRef")
async def scrape_ref(request: dataReq, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    content = scrape_paragraph_content(request.url)
    return {"reference": content}

@app.post("/addData")
async def add_data(request: dataStore, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    collection.insert_one(request.dict())
    return {"status":"Success", "code":200, "message": "Data saved successfully"}


@app.get("/getData")
async def get_data(
        x_api_key: str = Header(...),
        title: Optional[str] = Query(None, description="Title of newsletter")
):
    verify_api_key(x_api_key)
    result = collection.find_one({"title": title}, {"_id": 0})  # Exclude '_id' field from the result

    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"status": "Success", "code": 200, "data": result}

@app.get("/getAllData")
async def get_data(
        x_api_key: str = Header(...)
):
    verify_api_key(x_api_key)
    result = list(collection.find({}, {"_id": 0}))
    return {"status": "Success", "code": 200, "data": result}

@app.post("/sendEmail")
async def send_email(request: emailParams,x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    result = list(database["subscribers"].find({}, {"_id":0}))
    emails = result[0]['email']
    for doc in emails:
        send_email_with_alias(doc, request.link, request.title, request.des)
    return {"status":"Email sent successfully", "data": result[0]['email']}

@app.post("/addSub")
async def add_sub(request: addSub, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    data = list(database["subscribers"].find({}, {"_id":0}))
    data[0]["email"].append(f'{request.submail}')
    database["subscribers"].update_one({}, {"$set":{"email": data[0]["email"]}})
    return {"status_code":200, "data": data}

@app.post("/feedback")
async def add_sub(request: addFeedback, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    dbase = client["SAEWebsite"]
    collect = dbase["feedback"]
    collect.insert_one(request.dict())
    send_feedback_mail(request.username, request.message )
    return {"status_code":200, "message": "Feedback recorded"}


class userAuth(BaseModel):
    username: str
    password: str

@app.post("/auth")
async def authenticate(request: userAuth, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    result = database["userprofile"].find_one({"username": request.username, "password": request.password}, {"_id":0})

    if not result:
        raise HTTPException(status_code = 404, detail="invalid credentials")
    
    return {"message": "good credentials", "status":200}

@app.get("/")
async def root():
    return "Server working fine!!"