import smtplib
import requests
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SENDER_EMAIL = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.environ.get("EMAIL_ADDRESS")

# We use the Hacker News (Algolia) API - No Key Required!
# querying for: LLM, GPT, Transformer, Generative AI, Llama, CUDA, Python AI
QUERY = '"LLM" OR "OpenAI" OR "Transformer" OR "Llama" OR "RAG" OR "LangChain"'

def get_technical_news():
    # Calculate timestamp for 7 days ago
    seven_days_ago = int((datetime.now() - timedelta(days=7)).timestamp())
    
    # URL to search Hacker News for stories created in the last 7 days, 
    # sorted by points (popularity), filtering for our AI keywords
    url = (f'http://hn.algolia.com/api/v1/search_by_date?'
           f'query={QUERY}&'
           f'tags=story&'
           f'numericFilters=points>50,created_at_i>{seven_days_ago}&'
           f'hitsPerPage=15')
    
    try:
        response = requests.get(url)
        data = response.json()
        return data.get('hits', [])
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def create_html_email(articles):
    html_content = f"""
    <html>
    <body style="font-family: 'Verdana', sans-serif; max-width: 650px; margin: auto; color: #333;">
        <div style="background-color: #ff6600; padding: 15px; text-align: center;">
            <h2 style="color: white; margin:0;">Hacker News: AI Weekly</h2>
            <p style="color: white; font-size: 12px; margin:0;">For Developers & Engineers</p>
        </div>
        <div style="padding: 20px;">
    """
    
    for item in articles:
        title = item.get('title', 'No Title')
        url = item.get('url', '#')
        points = item.get('points', 0)
        author = item.get('author', 'unknown')
        comments_count = item.get('num_comments', 0)
        object_id = item.get('objectID')
        
        # Link to the actual article
        article_link = url
        # Link to the Hacker News discussion (often more valuable than the article!)
        discussion_link = f"https://news.ycombinator.com/item?id={object_id}"
        
        if not url or url == "#":
            article_link = discussion_link

        html_content += f"""
        <div style="margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px;">
            <div style="font-size: 16px; font-weight: bold;">
                <a href="{article_link}" style="text-decoration: none; color: #000;">{title}</a>
            </div>
            <div style="font-size: 12px; color: #828282; margin-top: 5px;">
                {points} points by {author} | 
                <a href="{discussion_link}" style="color: #ff6600; text-decoration: none; font-weight:bold;">
                    {comments_count} comments (Read Discussion)
                </a>
            </div>
        </div>
        """
        
    html_content += """
            <p style="text-align: center; color: #999; font-size: 12px; margin-top: 30px;">
                Generated via GitHub Actions
            </p>
        </div>
    </body>
    </html>
    """
    return html_content

def send_email():
    articles = get_technical_news()
    
    if not articles:
        print("No high-ranking AI news found this week.")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"👨‍💻 Dev AI Update: {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    html_body = create_html_email(articles)
    msg.attach(MIMEText(html_body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("Developer News sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    send_email()
