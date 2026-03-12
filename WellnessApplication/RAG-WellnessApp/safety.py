crisis_keywords = [
    'kill myself', 'suicide', 'end my life', 'want to die',
    'hurt myself', 'self harm', 'cut myself', 'end it all'
]

def check_crisis(text):
    text_lower = text.lower()
    for keyword in crisis_keywords:
        if keyword in text_lower:
            return True
    return False

def get_crisis_response():
    return """I'm very concerned about what you're sharing. Please reach out for immediate help:

Mental Health Helpline (TPO Nepal): 1660 01 02003 (Toll-free)
Mental Health Helpline (TUTH Psychiatry): 9840021600

Emergency Services:
- Police: 100
- Ambulance: 102
- Fire Brigade: 101

Support Helplines:
- Women's Helpline: 1145
- Child Helpline: 1098
- Disaster Management: 1130

You can also:
- Visit nearest emergency room (Teaching Hospital, Bir Hospital, etc.)
- Contact a mental health professional at:
  * Tribhuvan University Teaching Hospital (TUTH) Psychiatry Department
  * Transcultural Psychosocial Organization (TPO) Nepal
  * Centre for Mental Health and Counselling (CMC) Nepal

You're not alone. Help is available 24/7."""