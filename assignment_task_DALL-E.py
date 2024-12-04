import feedparser
import requests
from readability import Document
from transformers import pipeline
from bs4 import BeautifulSoup
import openai
import os

# API credentials
INSTAGRAM_ACCESS_TOKEN = "EABfwuAuOCQ8BO2dwvZASjZAwSacVkTH2iWorC3uBFgH5ebaIozHclCRu9ZCdUvZBEHZAInRPUUCvehAGDRnPEgxp7062kuoN3Dzn9sjsrMn4mPZBgX0a5afDLpaEveZBrsaZCheqkw25JxSX4qp1kyGjggoNT8Tvkmw1dWGKv1wrZBZCKabGofd8sVeYULmdA5u7TIOAJmUOWJbL0Mvmix2ZBm158HZA48PT"
INSTAGRAM_USER_ID = "17841441123508895"
openai.api_key = "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"

# Function to download and save image locally (not used for DALL-E, but kept for safety)
def download_image(image_url, save_path):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return save_path
        else:
            raise Exception(f"Failed to download image. HTTP Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

# Function to generate an image using OpenAI's DALL-E
def generate_image(prompt):
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        return response['data'][0]['url']
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

# Function to shorten URLs
def shorten_url(url):
    try:
        response = requests.get(f"http://tinyurl.com/api-create.php?url={url}")
        return response.text
    except Exception as e:
        print(f"Error shortening URL: {e}")
        return url

# 1. Detect new articles using RSS feed
def get_latest_article(rss_url):
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        raise Exception("No articles found in the RSS feed.")
    latest_entry = feed.entries[0]
    return {
        "title": latest_entry.title,
        "link": latest_entry.link,
        "summary": latest_entry.summary if 'summary' in latest_entry else None
    }

# 2. Extract article content and clean up HTML
def extract_article_content(url):
    response = requests.get(url)
    doc = Document(response.text)
    article_content = doc.summary()
    soup = BeautifulSoup(article_content, "html.parser")
    return soup.get_text()

# 3. Generate Instagram caption
def generate_caption(article_text, article_url):
    try:
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        summary = summarizer(article_text, max_length=50, min_length=10, do_sample=False)
        shortened_url = shorten_url(article_url)
        caption = f"{summary[0]['summary_text']} Read more: {shortened_url}"
        
        # Print the generated caption and shortened URL
        print(f"Generated Caption: {caption}")
        print(f"Shortened URL: {shortened_url}")
        
        return caption
    except Exception as e:
        print(f"Error generating caption: {e}")
        fallback_caption = f"Check out this article: {shorten_url(article_url)}"
        print(f"Fallback Caption: {fallback_caption}")
        return fallback_caption

# 4. Publish to Instagram
def post_to_instagram(image_url, caption):
    try:
        image_filename = "temp_image.jpg"
        
        
        saved_image_path = download_image(image_url, image_filename)
        if not saved_image_path:
            raise Exception("Failed to download image for Instagram post.")
        
        # Upload media
        media_upload_url = f"https://graph.facebook.com/v16.0/{INSTAGRAM_USER_ID}/media"
        media_data = {"image_url": image_url, "caption": caption, "access_token": INSTAGRAM_ACCESS_TOKEN}
        media_response = requests.post(media_upload_url, data=media_data)
        if media_response.status_code != 200:
            raise Exception(f"Error uploading media: {media_response.status_code} - {media_response.text}")
        
        media_id = media_response.json().get("id")
        if not media_id:
            raise Exception("No media ID returned from Instagram.")
    
        publish_url = f"https://graph.facebook.com/v16.0/{INSTAGRAM_USER_ID}/media_publish"
        publish_data = {"creation_id": media_id, "access_token": INSTAGRAM_ACCESS_TOKEN}
        publish_response = requests.post(publish_url, data=publish_data)
        if publish_response.status_code != 200:
            raise Exception(f"Error publishing media: {publish_response.status_code} - {publish_response.text}")
        
        print("Successfully posted to Instagram.")
    except Exception as e:
        print(f"Error during Instagram post: {e}")

# 5. Automate the process
def automate_instagram_post(rss_url):
    try:
        article = get_latest_article(rss_url)
        article_content = extract_article_content(article["link"])
        
        # Always generate an image using DALL-E
        print("Generating image with DALL-E...")
        image_url = generate_image(article["title"])
        if not image_url:
            raise Exception("Failed to generate an image.")
        
        # Generate caption and print it
        caption = generate_caption(article_content, article["link"])
        
      
        post_to_instagram(image_url, caption)
    except Exception as e:
        print(f"Error: {e}")

# Run the automation
if __name__ == "__main__":
    RSS_FEED_URL = "https://variety.com/feed/"
    automate_instagram_post(RSS_FEED_URL)
