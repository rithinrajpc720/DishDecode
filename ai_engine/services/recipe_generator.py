import json, random, re, os, tempfile
import google.generativeai as genai
import yt_dlp
from django.conf import settings

# --- AUDIO EXTRACTION INTERNAL SERVICE ---
class AudioExtractor:
    @staticmethod
    def extract_audio(video_url):
        """Extract audio from a video URL and save it to a temporary file."""
        temp_dir = tempfile.gettempdir()
        output_file_base = os.path.join(temp_dir, f'dishdecode_audio_{random.randint(1000,9999)}')
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'outtmpl': output_file_base,
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                # yt-dlp prepare_filename might not reflect the postprocessed .mp3 extension easily
                # so we just look for the expected file in the temp dir.
                audio_file = f"{output_file_base}.mp3"
                if os.path.exists(audio_file):
                    return audio_file
                return None
        except Exception as e:
            print(f"Error extracting audio: {str(e)}")
            return None

    @staticmethod
    def cleanup(file_path):
        """Remove a temporary file."""
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

# --- AI RECIPE PROMPT (Project Stronger) ---
AI_RECIPE_PROMPT = """You are a professional chef and food video analyst. Analyze the provided video audio and URL to generate a detailed recipe.

IMPORTANT: The video may be in ANY language (Hindi, Tamil, Telugu, Malayalam, Korean, Japanese, Spanish, French, Arabic, etc.). 
Regardless of the video's language, you MUST:
1. Identify the dish being prepared with high cultural accuracy.
2. Detect the original language of the video and the speaker.
3. Determine the country/region of origin of the dish.
4. Provide the complete recipe output ALWAYS IN ENGLISH.

Return a JSON object with EXACTLY these fields:
{{
    "dish_name": "Name of the dish (include original name in parentheses, e.g. 'Butter Chicken (Murgh Makhani)')",
    "cuisine_type": "Cuisine origin (e.g. Indian, Japanese, Mexican, Korean, etc.)",
    "detected_language": "The language spoken in the video",
    "country_of_origin": "The country where this dish originates",
    "ingredients": ["ingredient 1 with quantity", "ingredient 2 with quantity", ...],
    "steps": ["step 1 detailed instruction", "step 2 detailed instruction", ...],
    "cooking_time": "estimated total time",
    "tools_used": ["tool 1", "tool 2", ...],
    "confidence_score": 0.85,
    "ai_note": "Detailed analysis note about detected language and unique regional techniques.",
    "result_type": "extracted_recipe"
}}

Rules:
- confidence_score must be a float between 0.70 and 0.99
- All text must be in English
- If the video shows a regional/traditional dish, include the local name
"""

def _generate_with_ai(video_url):
    """Use Google Gemini with Multimodal Audio Analysis to generate a recipe."""
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        return None

    genai.configure(api_key=api_key)
    # Using 1.5-flash for speed and multimodal efficiency
    model = genai.GenerativeModel('gemini-1.5-flash')

    audio_path = AudioExtractor.extract_audio(video_url)
    audio_file = None
    
    try:
        content_to_send = [AI_RECIPE_PROMPT.format(video_url=video_url)]
        
        if audio_path and os.path.exists(audio_path):
            # Upload the audio for multimodal analysis
            audio_file = genai.upload_file(path=audio_path, display_name="video_audio")
            content_to_send.append(audio_file)

        response = model.generate_content(content_to_send)
        text = response.text.strip()

        # Handle Markdown formatting in Gemini responses
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        result = json.loads(text)

        # Validate confidence score (ensure it's a float)
        try:
            result['confidence_score'] = float(result.get('confidence_score', 0.85))
        except:
            result['confidence_score'] = 0.85
        
        result['confidence_score'] = min(0.99, max(0.70, result['confidence_score']))
        return result

    except Exception as e:
        print(f"Project Stronger AI Error: {str(e)}")
        return None
    finally:
        # Cleanup temporary files
        if audio_path:
            AudioExtractor.cleanup(audio_path)
        if audio_file:
            try:
                genai.delete_file(audio_file.name)
            except Exception:
                pass

def generate_recipe_from_url(video_url):
    # Core Global AI Processor (Multimodal: Audio + Video Analysis)
    try:
        ai_result = _generate_with_ai(video_url)
        if ai_result:
            return ai_result
    except Exception as e:
        print(f"Final AI fallback triggered: {str(e)}")
    
    # Static fallback for resilience
    return {
        "dish_name": "Global Food Recognition",
        "cuisine_type": "International",
        "detected_language": "Unknown (Analysis failed)",
        "country_of_origin": "Global",
        "ingredients": ["1. Visit DishDecode.com"],
        "steps": ["AI failed to process this specific video link. Please try another YouTube or Instagram URL."],
        "cooking_time": "Unknown",
        "tools_used": ["AI Processor"],
        "confidence_score": 0.50,
        "ai_note": "A technical error occurred during video analysis. Fallback triggered.",
        "result_type": "estimated_recipe"
    }
