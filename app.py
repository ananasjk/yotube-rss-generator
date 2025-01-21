from flask import Flask, request, render_template, session, jsonify
import re
import requests

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Required for session management

def get_channel_id_from_custom_url(custom_url):
    # Ensure the URL starts with https://
    if not custom_url.startswith("http"):
        custom_url = "https://" + custom_url

    try:
        # Fetch the raw HTML of the webpage
        response = requests.get(custom_url)
        response.raise_for_status()  # Raise an error for bad status codes
        html_content = response.text

        # Regex to find the canonical channel URL in the HTML
        channel_url_pattern = r'"https://www\.youtube\.com/channel/([a-zA-Z0-9_-]+)"'
        match = re.search(channel_url_pattern, html_content)

        if match:
            # Extract the channel ID from the matched URL
            return match.group(1)
        else:
            return None

    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None

def generate_rss_feed_link(channel_id):
    # Construct the RSS feed URL using the channel ID
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

@app.route("/", methods=["GET"])
def index():
    # Initialize the history list in the session if it doesn't exist
    if "history" not in session:
        session["history"] = []
    return render_template("index.html", history=session.get("history", []))

@app.route("/generate", methods=["POST"])
def generate():
    custom_url = request.form.get("youtube_url", "").strip()

    if custom_url:
        # Extract the username/handle from the URL
        handle = custom_url.split("@")[-1].split("/")[0] if "@" in custom_url else "unknown"

        channel_id = get_channel_id_from_custom_url(custom_url)

        if channel_id:
            rss_feed_link = generate_rss_feed_link(channel_id)
            # Add the result to the history
            new_entry = {"handle": handle, "rss_link": rss_feed_link}
            if "history" not in session:
                session["history"] = []
            session["history"].insert(0, new_entry)  # Add new entry at the top
            session.modified = True  # Ensure the session is saved
            return jsonify(success=True, entry=new_entry)
        else:
            return jsonify(success=False, error="No channel ID found in the webpage. Please check the URL.")
    else:
        return jsonify(success=False, error="Please enter a valid YouTube URL.")

@app.route("/clear", methods=["POST"])
def clear_history():
    # Clear the history
    session.pop("history", None)
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(debug=True)