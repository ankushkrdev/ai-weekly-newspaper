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

def get_technical_news():
    # 1. Get timestamp for 7 days ago
    seven_days_ago = int((datetime.now() - timedelta(days=7)).timestamp())
    
    # 2. ASK FOR EVERYTHING: Get top 100 stories from the last week with >50 points
    # We are NOT filtering by keyword here to avoid API errors.
    url = 'http://hn.algolia.com/api/v1/search'
    params = {
        'tags': 'story',
        'numericFilters': f'created_at_i>{seven_days_ago},points>50',
        'hitsPerPage': 100 
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        all_stories = data.get('hits', [])
        
        # 3. FILTER IN PYTHON: We look for AI keywords ourselves
        ai_keywords = [
            "ai", "artificial intelligence", "llm", "large language model",
            "gpt", "openai", "transformer", "llama", "mistral", "rag",
            "neural", "machine learning", "deep learning", "cuda", "nvidia",
            "generative", "stable diffusion", "midjourney", "chatbot",
            "anthropic", "claude", "gemini", "copilot", "hugging face",
            "github", "open source", "paper" # Added generic tech terms that often relate to AI
        ]

        filtered_stories = []
        for story in all_stories:
            title = story.get('title', '').lower()
            # If the title contains ANY of our keywords, keep it
            if any(keyword in title for keyword in ai_keywords):
                filtered_stories.append(story)
        
        # Return the top 10 matches (sorted by points)
        return filtered_stories[:10]
        
    except Exception as e:
        print(f"API Error: {e}")
        return []

def create_html_email(articles):
    date_str = datetime.now().strftime('%B %d, %Y')
    
    html_content = f"""
    <html>
    <body style="font-family: 'Verdana', sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <div style="border-bottom: 2px solid #ff6600; padding-bottom: 15px; margin-bottom: 25px;">
                <h1 style="color: #333; margin:0; font-size: 24px;">The AI Engineer</h1>
                <p style="color: #666; font-size: 14px; margin:5px 0 0 0;">Weekly Technical Digest • {date_str}</p>
            </div>
    """
    
    if not articles:
        html_content += """
        <p style="color: #666;">No specific AI headlines found this week. Check Hacker News directly.</p>
        """
    
    for item in articles:
        title = item.get('title', 'No Title')
        url = item.get('url')
        points = item.get('points', 0)
        comments = item.get('num_comments', 0)
        object_id = item.get('objectID')
        
        hn_link = f"https://news.ycombinator.com/item?id={object_id}"
        if not url: url = hn_link

        html_content += f"""
        <div style="margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee;">
            <div style="font-size: 18px; font-weight: 600; margin-bottom: 5px;">
                <a href="{url}" style="text-decoration: none; color: #2c3e50;">{title}</a>
            </div>
            <div style="font-size: 12px; color: #7f8c8d;">
                <span style="background-color: #ff6600; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{points} pts</span>
                <span style="margin: 0 8px;">•</span>
                <a href="{hn_link}" style="color: #3498db; text-decoration: none; font-weight: bold;">
                    Read {comments} Comments (Discussion)
                </a>
            </div>
        </div>
        """
        
    html_content += """
            <div style="text-align: center; margin-top: 40px; color: #aaa; font-size: 12px;">
                Automated by GitHub Actions
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

def send_email():
    print("Fetching top stories...")
    articles = get_technical_news()
    print(f"Found {len(articles)} relevant AI articles.")
    
    if not articles:
        print("No articles found after filtering.")
        # Optional: You could send an email saying "No news this week" if you wanted.
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"AI Engineer Weekly: {len(articles)} New Updates"
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
