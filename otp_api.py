from fastapi import FastAPI
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
import random, os, mysql.connector
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://otp-api-kc55.onrender.com"], 
    allow_credentials=False,    # change these origin, methods, setting after deploy othewise it will attract the hackers
    allow_methods=["*"],  
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"your api is working"}

@app.post("/send_otp")
def send_otp(to_email:str = Body(...)):
    try:
        db = mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_DATABASE"),
        port=int(os.environ.get("DB_PORT"))
        )

        cursor = db.cursor()
    
        cursor.execute("""
            delete from email_otp
            where expires_at < NOW()
        """)
        db.commit()

        cursor.execute("""
            select email from users
            where email = %s
        """, (to_email,))
        already_user=cursor.fetchone()

        if already_user:
            cursor.execute("""
            SELECT otp FROM email_otp
            WHERE email = %s AND expires_at > NOW()
            """, (to_email,))
            existing=cursor.fetchone()
            if not existing:
                configuration = sib_api_v3_sdk.Configuration()
                configuration.api_key['api-key'] = os.environ.get("BREVO_API_KEY")
    
                api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
                )
    
                otp=random.randint(1000,9999)

                email = sib_api_v3_sdk.SendSmtpEmail(
                    to=[{"email": to_email}],
                    sender={"email": "bitlx4@gmail.com", "name":    "Bit-LX"},
                    subject="Your OTP for login",
                    html_content=f"""
                    <h3>Your OTP is:</h3>
                    <h1>{otp}</h1>
                    <p>This OTP will expire in 5 minutes.</p>
                    """
                )

                try:
                    api_instance.send_transac_email(email)
                    cursor.execute("""
                    INSERT INTO email_otp (email, otp, expires_at)
                    VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL 5 MINUTE))
                    """, (to_email, otp))
                    db.commit()
                    return{"message":"otp send succesfully"}
        
                except ApiException as e:
                    return{"message":"otp not send ", "error":str(e)}
            else:
                return {"message": "OTP already exists"}
        else:
            return {"message": "user not found please sign up first"}
    finally:
        cursor.close()
        db.close()


    
        
