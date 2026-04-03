import json, random, re, os, tempfile, traceback
import google.generativeai as genai
import yt_dlp
from django.conf import settings

# --- VIDEO & AUDIO EXTRACTION INTERNAL SERVICE ---
class VideoProcessor:
    @staticmethod
    def download_video(video_url):
        """Download a low-resolution version of the video for multimodal analysis."""
        temp_dir = tempfile.gettempdir()
        # Create a unique filename for the mp4
        output_file_base = os.path.join(temp_dir, f'dishdecode_video_{random.randint(1000,9999)}')
        
        ydl_opts = {
            'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            'outtmpl': f"{output_file_base}.%(ext)s",
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(video_url, download=True)
                # Check for the expected mp4 file
                video_file = f"{output_file_base}.mp4"
                if os.path.exists(video_file):
                    return video_file
                return None
        except Exception as e:
            print(f"Deep Analysis Warning (Video/Audio Download Failed): {str(e)}")
            return None

    @staticmethod
    def cleanup(file_path):
        """Remove a temporary file."""
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

# --- AI DEEP MULTIMODAL PROMPT (Global Recipe Intelligence) ---
AI_RECIPE_PROMPT = """You are a "Master Culinary AI & Visual Analyst." Your mission is to analyze the provided video link (and its visual/audio stream) to generate a 100% accurate, professional recipe.

DEEP ANALYSIS REQUIREMENTS:
1. VISUALS & OCR: "Read" any text that appears on the screen (ingredients lists, heat levels, notes). Identify the kitchen tools (e.g. Kadai, Air Fryer, Griddle), utensils, and the visual state of the food.
2. AUDIO & SPEAKING: Listen to any dialogue. Identify the language(s) spoken and any specific regional dialects (e.g., Hindi, Tamil, Telugu, Malayalam, Korean, Spanish, French, Arabic, etc.).
3. INGREDIENTS & QUANTITIES: List every ingredient used. If the video doesn't state quantities, use your expert culinary knowledge to provide the most likely amounts for the dish shown.
4. CULTURAL ORIGIN: Accurately identify the dish's name (local name in parentheses if it's regional, e.g., 'Hyderabadi Biryani'). Identify the country and specific region/state (e.g. Origin: South India, Kerala).

OUTPUT FORMAT: Return a JSON object with EXACTLY these fields:
{{
    "dish_name": "Full name with native regional name in parentheses",
    "cuisine_type": "Regional/National cuisine (e.g., Coastal Kerala, Oaxacan Mexican, Traditional Korean)",
    "detected_language": "Languages/Dialects spoken in video or text on screen",
    "country_of_origin": "Country and specific region",
    "ingredients": ["Expertly calculated ingredient 1", "Expertly calculated ingredient 2", ...],
    "steps": ["Highly detailed step 1", "Highly detailed step 2", ...],
    "cooking_time": "Estimated prep and cook time",
    "tools_used": ["Every tool visible or heard, e.g., Pressure Cooker, Spatula, Heavy Bottomed Pan"],
    "confidence_score": 0.95,
    "ai_note": "A summary of the video language/dialect, unique regional techniques discovered, and visual OCR notes.",
    "result_type": "extracted_recipe"
}}

Rules:
- You MUST provide the output strictly in ENGLISH.
- If the video has text on screen, PRIORITY should be given to that for accuracy.
- Be extremely precise with seasonings and cultural techniques.
"""

def _generate_with_ai(video_url):
    """Use Google Gemini Deep Multimodal Analysis to generate a 100% accurate recipe."""
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        print("Missing GOOGLE_API_KEY in settings.")
        return None

    genai.configure(api_key=api_key)
    
    # Dynamic Model Selection (avoids 'NotFound' errors by picking an available model)
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Prefer flash for visual multimodal efficiency
        gemini_models = [m for m in available_models if 'gemini-1.5-flash' in m] or \
                        [m for m in available_models if 'gemini' in m]
        
        if not gemini_models:
            print("No Gemini-compatible models found for this API key.")
            return None
            
        selected_model_name = gemini_models[0]
        model = genai.GenerativeModel(selected_model_name)
        print(f"Using Master AI Model: {selected_model_name}")
    except Exception as model_err:
        print(f"Error selecting models: {str(model_err)}")
        model = genai.GenerativeModel('models/gemini-1.5-flash')

    # Try video download for Deep Multimodal Analysis (requires ffmpeg)
    video_path = VideoProcessor.download_video(video_url)
    video_file = None
    
    try:
        content_to_send = [f"Video URL: {video_url}", AI_RECIPE_PROMPT]
        
        if video_path and os.path.exists(video_path):
            try:
                # Upload the visual/audio stream for deep analysis
                print(f"Initiating Deep Visual/Audio analysis for: {video_path}")
                video_file = genai.upload_file(path=video_path, display_name="video_source")
                content_to_send.append(video_file)
            except Exception as upload_err:
                print(f"Deep Analysis Multimodal Upload Failed (using URL metadata fallback): {str(upload_err)}")
                # Proceed without video if upload fails

        response = model.generate_content(content_to_send)
        if not response or not hasattr(response, 'text') or not response.text:
            print(f"Gemini returned an invalid response. Full response: {response}")
            return None

        text = response.text.strip()

        # Handle Markdown/JSON cleanup
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        text = re.sub(r'^[^{]*', '', text)
        text = re.sub(r'[^}]*$', '', text)

        result = json.loads(text)

        # Validate confidence (Targeting 100% accuracy)
        try:
            result['confidence_score'] = float(result.get('confidence_score', 0.95))
        except:
            result['confidence_score'] = 0.95
        
        result['confidence_score'] = min(0.99, max(0.80, result['confidence_score']))
        return result

    except Exception as e:
        print(f"Master AI Upgrade Error: {str(e)}")
        traceback.print_exc()
        return None
    finally:
        # Cleanup temporary files
        if video_path:
            VideoProcessor.cleanup(video_path)
        if video_file:
            try:
                genai.delete_file(video_file.name)
            except Exception:
                pass

def generate_recipe_from_url(video_url):
    # Core Global AI Processor (Multimodal: Visuals + Audio + OCR)
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
