import smtplib
import requests
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SENDER_EMAIL = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.environ.get("EMAIL_ADDRESS")

def get_technical_news():
    # 1. Get the timestamp for 7 days ago
    seven_days_ago = int((datetime.now() - timedelta(days=7)).timestamp())
    
    # 2. Define the search clearly
    # We search for a broad range of technical terms
    query_terms = "LLM OR OpenAI OR GPT OR Transformer OR RAG OR Llama OR Mistral OR Nvidia"
    
    # 3. Setup the API parameters using a dictionary (Safer than f-strings)
    params = {
        'query': query_terms,
        'tags': 'story',
        'numericFilters': f'created_at_i>{seven_days_ago},points>20', # Must be >20 points & newer than 7 days
        'hitsPerPage': 15
    }
    
    # 4. Use the 'search' endpoint (Sorts by Relevance/Popularity)
    url = 'http://hn.algolia.com/api/v1/search'
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        hits = data.get('hits', [])
        
        # Sort by points (highest first) just to be sure
        hits.sort(key=lambda x: x.get('points', 0), reverse=True)
        return hits
        
    except Exception as e:
        print(f"API Error: {e}")
        return []

def create_html_email(articles):
    # Determine header date
    date_str = datetime.now().strftime('%B %d, %Y')
    
    html_content = f"""
    <html>
    <body style="font-family: 'Verdana', sans-serif; background-color: #f6f6ef; padding: 20px;">
        <div style="max-width: 700px; margin: auto; background-color: white; border: 1px solid #dcdcdc; padding: 20px;">
            <div style="border-bottom: 2px solid #ff6600; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="color: #333; margin:0;">Hacker News: AI Edition</h2>
                <p style="color: #666; font-size: 12px; margin:5px 0 0 0;">Top Engineering Discussions • {date_str}</p>
            </div>
    """
    
    if not articles:
        html_content += "<p>No significant AI news found matching criteria this week.</p>"
    
    for item in articles:
        title = item.get('title', 'No Title')
        url = item.get('url')
        points = item.get('points', 0)
        author = item.get('author', 'unknown')
        comments = item.get('num_comments', 0)
        object_id = item.get('objectID')
        
        # Hacker News Discussion Link
        hn_link = f"https://news.ycombinator.com/item?id={object_id}"
        
        # If the post is a "Ask HN" or text post, it might not have a URL
        if not url:
            url = hn_link

        html_content += f"""
        <div style="margin-bottom: 25px;">
            <div style="font-size: 16px; font-weight: 600;">
                <a href="{url}" style="text-decoration: none; color: #000;">{title}</a>
            </div>
            <div style="font-size: 11px; color: #828282; margin-top: 4px;">
                <span style="color: #ff6600;">{points} points</span> 
                by {author} 
                <span style="margin: 0 5px;">|</span> 
                <a href="{hn_link}" style="color: #000; text-decoration: underline;">
                    {comments} comments (View Discussion)
                </a>
            </div>
        </div>
        """
        
    html_content += """
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #999; font-size: 11px;">
                Automated by GitHub Actions
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

def send_email():
    print("Fetching news...")
    articles = get_technical_news()
    print(f"Found {len(articles)} articles.")
    
    if not articles:
        print("Skipping email - no articles found.")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Weekly AI Engineering Update"
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
        print("Email sent successfully!")
    except Exception as e:
        print(f"SMTP Error: {e}")

if __name__ == "__main__":
    send_email()
