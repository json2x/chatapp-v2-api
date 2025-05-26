#!/usr/bin/env python3
"""
Script to generate sample conversation data for the chatapp-v2-api.
Creates 5 conversations with 10-20 messages each for a specific user.
"""

import os
import sys
import random
from datetime import datetime, timedelta
import uuid

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from misc.db import create_conversation, add_message, get_db_connection

# Constants
USER_ID = "usr_123456789"
NUM_CONVERSATIONS = 5
MIN_MESSAGES = 10
MAX_MESSAGES = 20
MODELS = ["gpt-4o-mini", "gpt-4o", "claude-3-5-haiku-20241022"]

# Sample conversation topics with initial user messages and system prompts
CONVERSATION_TOPICS = [
    {
        "title": "Learning Python Programming",
        "system_prompt": "You are a helpful programming tutor specializing in Python.",
        "first_message": "I want to learn Python programming. Where should I start?"
    },
    {
        "title": "Travel Planning for Japan",
        "system_prompt": "You are a travel advisor with expertise in Japanese culture and tourism.",
        "first_message": "I'm planning a trip to Japan next month. What are the must-visit places in Tokyo?"
    },
    {
        "title": "Healthy Meal Prep Ideas",
        "system_prompt": "You are a nutritionist specializing in healthy meal preparation.",
        "first_message": "I need some healthy meal prep ideas for a busy work week."
    },
    {
        "title": "Book Recommendations",
        "system_prompt": "You are a literary expert with knowledge of books across all genres.",
        "first_message": "Can you recommend some good science fiction books for someone who enjoyed 'Dune'?"
    },
    {
        "title": "Home Workout Routines",
        "system_prompt": "You are a fitness coach specializing in home workouts.",
        "first_message": "I want to start working out at home. What are some good routines for beginners?"
    },
    {
        "title": "Learning to Play Guitar",
        "system_prompt": "You are a guitar teacher with experience teaching beginners.",
        "first_message": "I just got my first guitar. How should I start learning to play?"
    },
    {
        "title": "Gardening Tips for Beginners",
        "system_prompt": "You are a gardening expert with knowledge of plants and gardening techniques.",
        "first_message": "I want to start a small vegetable garden. What are some easy vegetables to grow for beginners?"
    }
]

# Sample message pairs (user question followed by assistant response)
MESSAGE_PAIRS = [
    # Python conversation
    (
        "How do I install Python on my computer?",
        "You can download Python from the official website (python.org). For Windows, download the installer and make sure to check 'Add Python to PATH' during installation. For macOS, you can use Homebrew with 'brew install python', or download from the official site. For Linux, most distributions come with Python pre-installed, but you can use your package manager (like 'apt install python3' for Ubuntu)."
    ),
    (
        "What's the difference between Python 2 and Python 3?",
        "Python 3 is the current version and has several improvements over Python 2, which is no longer supported. Key differences include: print is a function in Python 3 (requiring parentheses), division operator returns float by default in Python 3, Unicode support is better in Python 3, and there are many new features like f-strings, async/await, and type hints. You should definitely use Python 3 for any new projects."
    ),
    (
        "How do I create a virtual environment in Python?",
        "You can create a virtual environment using the built-in 'venv' module. Run 'python -m venv myenv' to create a virtual environment named 'myenv'. To activate it, on Windows use 'myenv\\Scripts\\activate', and on macOS/Linux use 'source myenv/bin/activate'. This creates an isolated environment for your project dependencies."
    ),
    
    # Travel conversation
    (
        "What's the best time of year to visit Japan?",
        "Spring (March to May) and autumn (September to November) are generally considered the best times to visit Japan. Spring offers cherry blossoms (sakura), while autumn brings beautiful fall foliage. The weather is mild and comfortable during these seasons. Summer can be hot and humid with a rainy season in June, while winter is cold but offers great skiing in northern regions and fewer tourists in major cities."
    ),
    (
        "Do I need to know Japanese to travel there?",
        "While knowing some basic Japanese phrases is helpful and appreciated by locals, you can get by in major tourist areas with English. Many signs in Tokyo, Kyoto, and other tourist destinations are in both Japanese and English. Train stations usually have English announcements, and many restaurants in tourist areas have English menus or picture menus. Consider downloading a translation app like Google Translate to help with communication."
    ),
    (
        "What's the transportation system like in Japan?",
        "Japan has one of the best public transportation systems in the world. The train and subway networks are extensive, punctual, and clean. In Tokyo, the JR Yamanote Line loops around the city connecting major areas, and the subway reaches almost everywhere else. For traveling between cities, the Shinkansen (bullet train) is fast and efficient. Consider getting a Japan Rail Pass if you plan to travel between multiple cities, as it can save you money. IC cards like Suica or PASMO are convenient for local transportation."
    ),
    
    # Meal prep conversation
    (
        "How do I keep my meal prep interesting so I don't get bored?",
        "To keep meal prep interesting: 1) Rotate between different protein sources (chicken, fish, tofu, beans), 2) Use various cooking methods (roasting, steaming, sautéing), 3) Experiment with global flavors and spices (Mediterranean, Asian, Mexican), 4) Prep components rather than full meals to mix and match, 5) Include different textures in each meal, and 6) Allow yourself one or two new recipes each week. Also, consider theme nights like Taco Tuesday or Stir-Friday to add structure while maintaining variety."
    ),
    (
        "What are some good containers for meal prepping?",
        "Good meal prep containers include: 1) Glass containers with compartments (durable, microwave-safe, don't retain odors), 2) BPA-free plastic containers (lightweight, less expensive), 3) Stainless steel containers (durable but not microwave-safe), 4) Silicone bags for snacks and liquids (reusable, freezer-safe), and 5) Mason jars for salads and overnight oats. Look for leak-proof lids, stackability, and appropriately sized compartments for your portions."
    ),
    (
        "How long can I keep meal prepped food in the refrigerator?",
        "Most meal prepped foods can be safely stored in the refrigerator for 3-5 days. Seafood should be consumed within 1-2 days for best quality. Raw vegetables and fruits last about 5-7 days when properly stored. Cooked grains and legumes typically last 3-5 days. For longer storage, consider freezing portions (good for 2-3 months). Always use proper containers, cool food before refrigerating, and check for any signs of spoilage before consuming."
    ),
    
    # Books conversation
    (
        "What are some classic sci-fi novels everyone should read?",
        "Some essential classic sci-fi novels include: 1) 'Foundation' by Isaac Asimov, 2) 'Neuromancer' by William Gibson, 3) 'The Left Hand of Darkness' by Ursula K. Le Guin, 4) '1984' by George Orwell, 5) 'Brave New World' by Aldous Huxley, 6) 'Fahrenheit 451' by Ray Bradbury, 7) 'Slaughterhouse-Five' by Kurt Vonnegut, and 8) 'The War of the Worlds' by H.G. Wells. These works established many of the themes and concepts that continue to influence science fiction today."
    ),
    (
        "I enjoy books with complex political systems like in Dune. Any recommendations?",
        "If you enjoy complex political systems like in 'Dune,' you might like: 1) 'The Expanse' series by James S.A. Corey, 2) 'The Moon is a Harsh Mistress' by Robert A. Heinlein, 3) 'The Dispossessed' by Ursula K. Le Guin, 4) 'Too Like the Lightning' by Ada Palmer, 5) 'A Memory Called Empire' by Arkady Martine, 6) 'The Traitor Baru Cormorant' by Seth Dickinson, and 7) 'Red Rising' by Pierce Brown. These all feature intricate political machinations and power struggles in richly developed worlds."
    ),
    (
        "Who are some up-and-coming sci-fi authors I should check out?",
        "Some exciting newer sci-fi authors to check out include: 1) N.K. Jemisin (The Broken Earth trilogy), 2) Ted Chiang (Exhalation, Stories of Your Life and Others), 3) Martha Wells (The Murderbot Diaries), 4) Becky Chambers (Wayfarers series), 5) Tade Thompson (Rosewater), 6) Rivers Solomon (An Unkindness of Ghosts), 7) Arkady Martine (A Memory Called Empire), and 8) P. Djèlí Clark (Ring Shout, The Haunting of Tram Car 015). These authors are bringing fresh perspectives and innovative ideas to the genre."
    ),
    
    # Fitness conversation
    (
        "How often should I work out as a beginner?",
        "As a beginner, aim for 2-3 workouts per week with at least one rest day between sessions. This gives your body time to recover and adapt to the new stresses. Start with 20-30 minute sessions and gradually increase to 45-60 minutes as your fitness improves. Remember that consistency is more important than intensity when you're starting out. Listen to your body and don't push through pain (which is different from normal muscle fatigue)."
    ),
    (
        "Do I need any equipment for home workouts?",
        "You can get a great workout at home with minimal or no equipment. Bodyweight exercises like push-ups, squats, lunges, and planks are very effective. That said, a few inexpensive items can add variety: resistance bands ($10-20), a yoga mat ($20-30), a pair of adjustable dumbbells ($50-100), and a jump rope ($10-15). As you progress, you might consider a pull-up bar ($25-40) or kettlebell ($20-40). Start with basics and add equipment gradually as needed."
    ),
    (
        "How do I know if I'm making progress with my workouts?",
        "Track your progress through multiple metrics: 1) Performance improvements (more reps, heavier weights, better form, less rest needed), 2) Body composition changes (measurements, how clothes fit), 3) Energy levels and mood improvements, 4) Better sleep quality, 5) Increased everyday functional fitness (easier to climb stairs, carry groceries, etc.). Take photos and notes every 4 weeks, as day-to-day changes are subtle. Remember that progress isn't always linear—plateaus are normal and part of the journey."
    ),
    
    # Guitar conversation
    (
        "Should I learn on an acoustic or electric guitar?",
        "Both acoustic and electric guitars have advantages for beginners. Acoustic guitars are more portable, require no additional equipment, and build finger strength faster. Electric guitars have thinner strings that are easier on fingers, allow for lower action (string height), and can be played with headphones to avoid disturbing others. The best choice depends on your musical interests—if you love acoustic-based music (folk, singer-songwriter), start with acoustic. If you prefer rock, metal, or blues, an electric might be more motivating. The fundamental skills transfer between both types."
    ),
    (
        "How long should I practice each day?",
        "Quality matters more than quantity for guitar practice, especially for beginners. Start with 15-20 minutes of focused practice daily—this is more effective than one 2-hour session weekly. As you build calluses and hand strength, gradually increase to 30-45 minutes. Break practice into chunks: technique drills (5-10 min), new material (10-15 min), and review/play for fun (5-10 min). Consistency is key—daily short sessions lead to faster progress than occasional long ones. Listen to your body and rest if you experience pain beyond mild discomfort."
    ),
    (
        "What are the first chords I should learn?",
        "Start with these beginner-friendly open chords: E minor, A minor, D minor, C major, G major, and D major. These form the foundation for thousands of songs and introduce fundamental finger positions. Practice transitioning between them slowly and cleanly before increasing speed. Once comfortable, add A major and E major to your repertoire. Learn chord progressions like Em-C-G-D or C-G-Am-F, which are used in countless popular songs. Focus on clean sound (no buzzing or muted strings) rather than speed initially."
    ),
    
    # Gardening conversation
    (
        "How much sunlight do vegetables need?",
        "Most vegetables need at least 6-8 hours of direct sunlight daily for optimal growth. Leafy greens (lettuce, spinach, kale) can tolerate partial shade with 4-6 hours of sun. Fruiting vegetables (tomatoes, peppers, cucumbers) and root vegetables (carrots, radishes) require full sun (8+ hours) to produce well. Before planting, observe your garden space throughout the day to identify how sunlight moves across the area. Consider using a sun calculator app to track exact hours if you're unsure."
    ),
    (
        "When should I start planting my vegetable garden?",
        "Planting time depends on your local climate and the vegetables you're growing. Cool-season crops (lettuce, peas, radishes, spinach) can be planted 2-4 weeks before the last spring frost. Warm-season crops (tomatoes, peppers, cucumbers) should be planted after all danger of frost has passed. Check your local agricultural extension office website for a planting calendar specific to your region. You can also use the USDA Hardiness Zone map as a general guide, but local microclimates may vary."
    ),
    (
        "How often should I water my vegetable garden?",
        "Most vegetable gardens need about 1-1.5 inches of water per week, either from rainfall or irrigation. Rather than frequent shallow watering, aim for fewer deep waterings that encourage roots to grow deeper. Generally, watering deeply 2-3 times per week is better than daily light watering. Use the finger test—insert your finger 2 inches into the soil; if it feels dry, it's time to water. Morning watering is best as it reduces evaporation and fungal disease risk. Adjust based on weather conditions, soil type, and specific plant needs."
    )
]

def generate_sample_data():
    """Generate sample conversations and messages in the database."""
    print("Generating sample conversation data...")
    
    # Clear existing data for this user
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get existing conversation IDs for this user
        cursor.execute("SELECT id FROM conversations WHERE user_id = ?", (USER_ID,))
        existing_conversations = cursor.fetchall()
        
        # Delete existing conversations
        if existing_conversations:
            for conv in existing_conversations:
                cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv[0],))
                cursor.execute("DELETE FROM conversations WHERE id = ?", (conv[0],))
            
            conn.commit()
            print(f"Cleared {len(existing_conversations)} existing conversations for user {USER_ID}")
    
    # Sample conversation topics
    topics = random.sample(CONVERSATION_TOPICS, NUM_CONVERSATIONS)
    
    # Create conversations
    total_messages = 0
    for i, topic in enumerate(topics):
        # Create the conversation
        conversation_id = create_conversation(
            title=topic["title"],
            model=random.choice(MODELS),
            system_prompt=topic["system_prompt"],
            user_id=USER_ID
        )
        
        print(f"Created conversation {i+1}/{NUM_CONVERSATIONS}: {topic['title']}")
        
        # Determine number of message pairs for this conversation (each pair is user + assistant)
        # We want between MIN_MESSAGES and MAX_MESSAGES total messages
        # So divide by 2 for pairs, but ensure we have an odd number to end with assistant
        num_pairs = random.randint(MIN_MESSAGES // 2, MAX_MESSAGES // 2)
        
        # Add the first user message
        add_message(
            conversation_id=conversation_id,
            role="user",
            content=topic["first_message"],
            model=None
        )
        
        # Add first assistant response
        add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=f"I'd be happy to help you with {topic['title'].lower()}! {random.choice(MESSAGE_PAIRS)[1]}",
            model=random.choice(MODELS)
        )
        
        # Add additional message pairs
        used_pairs = set()
        for j in range(num_pairs - 1):  # -1 because we already added the first pair
            # Select a message pair that hasn't been used yet
            available_pairs = [(idx, pair) for idx, pair in enumerate(MESSAGE_PAIRS) if idx not in used_pairs]
            if not available_pairs:  # If all pairs have been used, reset
                used_pairs = set()
                available_pairs = [(idx, pair) for idx, pair in enumerate(MESSAGE_PAIRS)]
            
            pair_idx, (user_msg, assistant_msg) = random.choice(available_pairs)
            used_pairs.add(pair_idx)
            
            # Add user message
            add_message(
                conversation_id=conversation_id,
                role="user",
                content=user_msg,
                model=None
            )
            
            # Add assistant response
            add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_msg,
                model=random.choice(MODELS)
            )
        
        # Check if the last message is from the user, and if so, add an assistant response
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role FROM messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT 1",
                (conversation_id,)
            )
            last_role = cursor.fetchone()[0]
            
            if last_role == "user":
                # Add a final assistant response
                add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content="I hope that helps! Let me know if you have any other questions about " + topic["title"].lower() + ".",
                    model=random.choice(MODELS)
                )
                print(f"  Added a final assistant message to ensure assistant has the last word")
        
        # Count the total messages in this conversation
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE conversation_id = ?",
                (conversation_id,)
            )
            conversation_message_count = cursor.fetchone()[0]
            total_messages += conversation_message_count
            print(f"  Added {conversation_message_count} messages to conversation")
    
    print(f"Successfully generated {NUM_CONVERSATIONS} sample conversations with {total_messages} total messages")

if __name__ == "__main__":
    generate_sample_data()
