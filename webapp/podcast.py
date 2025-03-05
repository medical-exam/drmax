import streamlit as st
from googleapiclient.discovery import build

# YouTube API Key
YOUTUBE_API_KEY = "AIzaSyCXF_4_9F4FDzN5u9WEuNQZFkcNzH6mYVs"

def get_youtube_podcasts(query, max_results=3):
    """Fetches top YouTube videos based on a search query."""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=max_results
    )
    response = request.execute()

    video_data = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        video_data.append((title, f"https://www.youtube.com/watch?v={video_id}", video_id))

    return video_data

def extract_mood_from_report(report_text):
    """Extracts the mood from the generated mental health report."""
    mood_keywords = {
        "Happy": ["positive", "Happy", "content", "joyful"],
        "Sad": ["Sad", "depressed", "down", "low"],
        "Stressed": ["stressed","Stressed", "overwhelmed", "tense", "pressure", "burnout"],
        "Anxious": ["Anxious", "worried", "nervous", "fearful"],
        "Calm": ["Calm", "relaxed", "peaceful", "mindful"],
        "Neutral": ["Neutral"]
    }

    report_text = report_text.lower()
    detected_mood = "Neutral"  # Default mood

    for mood, keywords in mood_keywords.items():
        if any(keyword in report_text for keyword in keywords):
            detected_mood = mood
            break  # Stop searching after finding the first match

    return detected_mood  # Corrected return statement

def display_podcasts():
    st.title("🎙 Podcast Recommendations")

    if "analysis_result" in st.session_state and st.session_state.analysis_result:
        mood = extract_mood_from_report(st.session_state.analysis_result)

        # Debugging: Show extracted mood
        st.write(f"**Detected Mood:** {mood}")

        mood_queries = {
            "Happy": "motivational self-improvement podcasts",
            "Sad": "uplifting talks on overcoming sadness",
            "Stressed": "stress management techniques podcast",
            "Anxious": "calming mindfulness exercises for anxiety",
            "Calm": "deep relaxation and mindfulness meditation",
            "Neutral": "best mental health podcasts"
        }

        query = mood_queries.get(mood, "mental health podcast")
        podcasts = get_youtube_podcasts(query)

        st.subheader(f"🎧 Recommended Podcasts for '{mood.capitalize()}' Mood:")
        for title, link, video_id in podcasts:
            st.markdown(f"### {title}")
            st.video(f"https://www.youtube.com/embed/{video_id}")  # Embed video
            st.markdown("---")  # Separator
    else:
        st.warning("⚠️ Please generate your Mental Health Report first!")

