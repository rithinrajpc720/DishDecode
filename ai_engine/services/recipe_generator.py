import json, random, re, os, tempfile, traceback
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
                ydl.extract_info(video_url, download=True)
                audio_file = f"{output_file_base}.mp3"
                if os.path.exists(audio_file):
                    return audio_file
                return None
        except Exception as e:
            # log the error but don't crash; we will fallback to text-only analysis
            print(f"Audio Extraction Warning: {str(e)}")
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
AI_RECIPE_PROMPT = """You are a professional chef and food video analyst. Analyze the provided video URL {audio_context} to generate a detailed recipe.

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
    """Use Google Gemini with Multimodal Audio Analysis (or text fallback) to generate a recipe."""
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        print("Missing GOOGLE_API_KEY in settings.")
        return None

    genai.configure(api_key=api_key)
    
    # Dynamic Model Selection (avoids 'NotFound' errors by picking an available model)
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Prefer flash for speed, but fallback to any gemini model
        gemini_models = [m for m in available_models if 'gemini-1.5-flash' in m] or \
                        [m for m in available_models if 'gemini' in m]
        
        if not gemini_models:
            print("No Gemini-compatible models found for this API key.")
            return None
            
        selected_model_name = gemini_models[0]
        model = genai.GenerativeModel(selected_model_name)
        print(f"Using AI Model: {selected_model_name}")
    except Exception as model_err:
        print(f"Error listing/selecting models: {str(model_err)}")
        model = genai.GenerativeModel('models/gemini-1.5-flash') # Hard fallback

    # Try audio extraction (requires ffmpeg)
    audio_path = AudioExtractor.extract_audio(video_url)
    audio_file = None
    
    try:
        audio_context = "and its extracted audio" if audio_path else "(Analyzing via URL metadata fallback as audio extraction was skipped)"
        prompt = AI_RECIPE_PROMPT.format(audio_context=audio_context)
        
        content_to_send = [f"Video URL: {video_url}", prompt]
        
        if audio_path and os.path.exists(audio_path):
            try:
                # Upload the audio for multimodal analysis
                audio_file = genai.upload_file(path=audio_path, display_name="video_audio")
                content_to_send.append(audio_file)
                print(f"Successfully uploaded audio for analysis: {audio_path}")
            except Exception as upload_err:
                print(f"Gemini Audio Upload Failed: {str(upload_err)}")
                # Proceed without audio if upload fails

        response = model.generate_content(content_to_send)
        if not response or not hasattr(response, 'text') or not response.text:
            print(f"Gemini returned an invalid response. Full response: {response}")
            return None

        text = response.text.strip()

        # Handle Markdown formatting in Gemini responses
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        # Final cleanup for potential leading/trailing non-json chars
        text = re.sub(r'^[^{]*', '', text)
        text = re.sub(r'[^}]*$', '', text)

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
        traceback.print_exc() # Print full traceback to console for debugging
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
        traceback.print_exc()
    
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
def validate_video_url(url):
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+',
    ]
    instagram_patterns = [
        r'(?:https?://)?(?:www\.)?instagram\.com/reel/[\w-]+',
        r'(?:https?://)?(?:www\.)?instagram\.com/reels/[\w-]+',
        r'(?:https?://)?(?:www\.)?instagram\.com/p/[\w-]+',
    ]
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True, 'youtube'
    for pattern in instagram_patterns:
        if re.match(pattern, url):
            return True, 'instagram'
    return False, None

def detect_platform(url):
    if 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    if 'instagram.com' in url:
        return 'instagram'
    return 'unknown'
