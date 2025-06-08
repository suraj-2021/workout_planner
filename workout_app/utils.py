import os
import smtplib
import razorpay
import requests
import hmac
import hashlib
import json
from django.conf import settings


from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
import telegram
import discord
from dotenv import load_dotenv

load_dotenv()

# Gmail configuration
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')  # App password, not regular password

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Discord configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')


# Razorpay configuration
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')

# Cashfree configuration
CASHFREE_CLIENT_ID = os.getenv('CASHFREE_CLIENT_ID')
CASHFREE_CLIENT_SECRET = os.getenv('CASHFREE_CLIENT_SECRET')
CASHFREE_BASE_URL = os.getenv('CASHFREE_BASE_URL', 'https://sandbox.cashfree.com')  # Use production URL for live


def send_email(recipient_email, subject, message):
    """Send email using Gmail SMTP"""
    if not all([GMAIL_USER, GMAIL_PASSWORD, recipient_email]):
        return False, "Missing email configuration"
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Attach message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        return True, "Email sent successfully"
    except Exception as e:
        return False, f"Error sending email: {str(e)}"

async def send_telegram_message(chat_id, message):
    """Send message via Telegram bot"""
    if not all([TELEGRAM_BOT_TOKEN, chat_id]):
        return False, "Missing Telegram configuration"
    
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        return True, "Telegram message sent successfully"
    except Exception as e:
        return False, f"Error sending Telegram message: {str(e)}"

# Helper function to run async telegram function
def send_telegram(chat_id, message):
    """Run async telegram function"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(send_telegram_message(chat_id, message))
    loop.close()
    return result

async def send_discord_dm(user_id, message):
    """Send direct message via Discord bot"""
    if not all([DISCORD_BOT_TOKEN, user_id]):
        return False, "Missing Discord configuration"
    
    try:
        # Create Discord client
        intents = discord.Intents.default()
        intents.messages = True
        client = discord.Client(intents=intents)
        
        # Define event handler
        @client.event
        async def on_ready():
            try:
                # Get user object
                user = await client.fetch_user(int(user_id))
                
                # Send DM
                await user.send(message)
            except Exception as e:
                print(f"Error in Discord DM: {e}")
            finally:
                # Close client connection
                await client.close()
        
        # Run Discord bot
        await client.start(DISCORD_BOT_TOKEN)
        return True, "Discord message sent successfully"
    except Exception as e:
        return False, f"Error sending Discord message: {str(e)}"

# Helper function to run async discord function
def send_discord(user_id, message):
    """Run async discord function"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(send_discord_dm(user_id, message))
    loop.close()
    return result


class RazorpayHandler:
    def __init__(self):
        self.client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    
    def create_order(self, amount, currency='INR', receipt=None):
        """Create a Razorpay order"""
        try:
            order_data = {
                'amount': int(amount * 100),  # Amount in paise
                'currency': currency,
                'receipt': receipt or f'receipt_{int(amount)}',
                'payment_capture': 1  # Auto capture
            }
            order = self.client.order.create(data=order_data)
            return True, order
        except Exception as e:
            return False, str(e)

    def verify_payment(self, payment_id, order_id, signature):
        """Verify Razorpay payment signature"""
        try:
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            self.client.utility.verify_payment_signature(params_dict)
            return True, "Payment verified successfully"
        except Exception as e:
            return False, str(e)

class CashfreeHandler:
    def __init__(self):
        self.client_id = CASHFREE_CLIENT_ID
        self.client_secret = CASHFREE_CLIENT_SECRET
        self.base_url = CASHFREE_BASE_URL
        self.headers = {
            'Content-Type': 'application/json',
            'x-client-id': self.client_id,
            'x-client-secret': self.client_secret
        }
    
    def create_order(self, amount, order_id, customer_details, return_url, notify_url):
        """Create a Cashfree order"""
        try:
            order_data = {
                "order_amount": float(amount),
                "order_currency": "INR",
                "order_id": order_id,
                "customer_details": customer_details,
                "order_meta": {
                    "return_url": return_url,
                    "notify_url": notify_url
                }
            }
            
            response = requests.post(
                f"{self.base_url}/pg/orders",
                headers=self.headers,
                json=order_data
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, response.text
        except Exception as e:
            return False, str(e)

    def verify_payment(self, order_id):
        """Verify Cashfree payment"""
        try:
            response = requests.get(
                f"{self.base_url}/pg/orders/{order_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, response.text
        except Exception as e:
            return False, str(e)

    def verify_webhook_signature(self, payload, signature, timestamp):
        """Verify Cashfree webhook signature"""
        try:
            # Create the signature string
            signature_string = f"{timestamp}.{payload}"
            
            # Generate HMAC signature
            computed_signature = hmac.new(
                self.client_secret.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, computed_signature)
        except Exception as e:
            return False


# Utility functions
def get_payment_handler(provider):
    """Get the appropriate payment handler"""
    if provider == 'razorpay':
        return RazorpayHandler()
    elif provider == 'cashfree':
        return CashfreeHandler()
    else:
        raise ValueError(f"Unsupported payment provider: {provider}")

def format_currency(amount):
    """Format currency for display"""
    return f"₹{amount:,.2f}"
