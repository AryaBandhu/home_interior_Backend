import requests
import base64
from decouple import config

AI_API_KEY = config('AI_API_KEY', default='')
AI_API_URL = config('AI_API_URL', default='')
AI_MODEL = config('AI_MODEL', default='')


def encode_image_to_base64(image_path):
    """Convert local image file to base64 string"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def generate_images(image_path, prompt, num_samples=1):
    """
    Main entry point for image generation.
    Automatically uses mock if no API key set.
    """
    if not AI_API_KEY or not AI_API_URL:
        return _mock_response(num_samples)

    return _call_ai_api(image_path, prompt, num_samples)


def _mock_response(num_samples):
    """Used when no API key is configured"""
    return {
        'success': True,
        'image_urls': [
            f'https://picsum.photos/512/512?random={i}'
            for i in range(num_samples)
        ],
        'image_b64_list': [],
    }


def _call_ai_api(image_path, prompt, num_samples=1):
    try:
        image_b64 = encode_image_to_base64(image_path)

        if 'generativelanguage.googleapis.com' in AI_API_URL:
            return _call_gemini(image_b64, prompt, num_samples)
        else:
            return _call_custom_api(image_b64, prompt, num_samples)

    except Exception as e:
        return {'success': False, 'error': str(e)}


def _call_gemini(image_b64, prompt, num_samples=1):
    """Gemini image generation — used for testing"""
    try:
        response = requests.post(
            AI_API_URL,
            headers={
                'x-goog-api-key': AI_API_KEY,
                'Content-Type': 'application/json',
            },
            json={
                'contents': [{
                    'parts': [
                        {'text': prompt},
                        {
                            'inline_data': {
                                'mime_type': 'image/jpeg',
                                'data': image_b64,
                            }
                        }
                    ]
                }],
                'generationConfig': {
                    'responseModalities': ['image', 'text'],
                }
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        # parse gemini response
        parts = data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
        image_b64_list = [
            p['inlineData']['data']
            for p in parts
            if 'inlineData' in p
        ]

        if not image_b64_list:
            return {'success': False, 'error': 'No images returned from Gemini'}

        return {
            'success': True,
            'image_b64_list': image_b64_list[:num_samples],
            'image_urls': [],
        }

    except requests.exceptions.HTTPError as e:
        return {'success': False, 'error': f'Gemini error: {str(e)} — {e.response.text}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _call_custom_api(image_b64, prompt, num_samples=1):
    """
    Custom API (NanoBanna or any other) — used in production.
    Update payload as per API docs.
    """
    try:
        payload = {
            'model': AI_MODEL,
            'prompt': prompt,
            'image': image_b64,
            'num_images': num_samples,
            'width': 1024,
            'height': 1024,
        }

        headers = {
            'Authorization': f'Bearer {AI_API_KEY}',
            'Content-Type': 'application/json',
        }

        response = requests.post(
            AI_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        # check if polling needed
        task_id = data.get('id') or data.get('task_id') or data.get('request_id')
        if task_id:
            return _poll_for_result(task_id)

        return _parse_direct_response(data, num_samples)

    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'API request timed out'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Could not connect to AI API'}
    except requests.exceptions.HTTPError as e:
        return {'success': False, 'error': f'API error: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _parse_direct_response(data, num_samples):
    image_urls = (
        data.get('images') or
        data.get('output') or
        data.get('urls') or
        [data.get('result', {}).get('url')]
    )

    if not image_urls:
        return {'success': False, 'error': 'No images in response'}

    return {
        'success': True,
        'image_urls': image_urls[:num_samples],
        'image_b64_list': [],
    }


def _poll_for_result(task_id, max_attempts=30, interval=3):
    import time
    poll_url = config('AI_POLL_URL', default=AI_API_URL + '/result')

    for _ in range(max_attempts):
        time.sleep(interval)
        try:
            response = requests.get(
                poll_url,
                headers={'Authorization': f'Bearer {AI_API_KEY}'},
                params={'id': task_id},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            status = data.get('status') or data.get('state')

            if status in ['Ready', 'succeeded', 'completed', 'done']:
                return _parse_direct_response(data, num_samples=10)

            if status in ['Failed', 'failed', 'error']:
                return {'success': False, 'error': 'Generation failed'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    return {'success': False, 'error': 'Generation timed out'}