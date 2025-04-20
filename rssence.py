import feedparser
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from openai import OpenAI
import time
import os
import toml

# Configuration
CONFIG_FILE = "config.toml"

# Function to fetch and summarize an article
def fetch_and_summarize_article(url, api_url, api_key, ai_model):
    try:
        # Fetch the article content
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        article_content = soup.get_text()

        # Send the content to the Perplexity API for summarization
        client = OpenAI(api_key=api_key, base_url=api_url)
        payload = {"text": article_content}
        response = client.chat.completions.create(
            model=ai_model,
            messages=[
                {"role": "user", "content": f"Summarize the following article: {payload}"}
            ],
            max_tokens=1000
        )
        return response.choices[0].message['content']
    except Exception as e:
        print(f"Error summarizing article: {e}")
        return "Error summarizing this article."

# Function to monitor multiple RSS feeds and generate new feeds
def monitor_rss_feeds(config):
    seen_entries = {feed_url: set() for feed_url in config["feeds"]}
    feed_generators = {}

    for feed_url in config["feeds"]:
        fg = FeedGenerator()
        fg.title(f"Summarized RSS Feed for {feed_url}")
        fg.link(href=feed_url, rel="self")
        fg.description("A feed with summarized articles.")
        feed_generators[feed_url] = fg

    while True:
        for feed_url in config["feeds"]:
            feed = feedparser.parse(feed_url)
            fg = feed_generators[feed_url]

            # Get the entries, limiting to the most recent 10 if this is the first query
            entries = feed.entries
            if not seen_entries[feed_url]:
                entries = entries[:10]  # Only process the most recent 10 entries initially

            for entry in entries:
                if entry.id not in seen_entries[feed_url]:
                    seen_entries[feed_url].add(entry.id)
                    print(f"Processing new entry from {feed_url}: {entry.title}")
                    summary = fetch_and_summarize_article(entry.link, config["api_url"], config["api_key"], config["ai_model"])
                    fe = fg.add_entry()
                    fe.title(entry.title)
                    fe.link(href=entry.link)
                    fe.description(summary)

            # Write the updated feed to a file
            output_file = f"data/summarized_feed_{feed_url.replace('://', '_').replace('/', '_')}.xml"
            fg.rss_file(output_file)
            print(f"Updated feed written to {output_file}")

        # Wait before polling again
        time.sleep(config["poll_interval"])

if __name__ == "__main__":    
    if not os.path.exists(CONFIG_FILE):
        print(f"Configuration file '{CONFIG_FILE}' not found.")
        exit(1)
    print(f"Loading configuration from '{CONFIG_FILE}'...")
    config = toml.load(CONFIG_FILE)
    print("Starting to monitor RSS feeds...")
    monitor_rss_feeds(config)
