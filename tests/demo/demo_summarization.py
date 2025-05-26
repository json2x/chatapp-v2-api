#!/usr/bin/env python3
"""
Demonstration script for testing the conversation summarization functionality.
This script demonstrates how to use the brief_summary_of_conversation_history function
with different types of conversations and media content.

Usage:
    python demo_summarization.py simple
    python demo_summarization.py media
    python demo_summarization.py technical
    python demo_summarization.py compare
"""

import os
import sys
import time
import argparse
from typing import Dict, List, Any
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the LLM service wrapper
from llm_service_providers.index import llm_service
from misc.constants import Provider, DEFAULT_MODELS

# Load environment variables from .env file
load_dotenv()


def display_summary(title, messages):
    """Display a summary of the given conversation."""
    print("\n" + "="*80)
    print(f"{title}")
    print(f"Using model: gpt-4o-mini")
    print("="*80)
    
    print("\nOriginal Conversation:")
    print("-" * 40)
    for msg in messages:
        role = msg["role"].upper()
        content = msg["content"]
        print(f"{role}: {content[:100]}{'...' if len(content) > 100 else ''}")
    
    print("\nGenerating summary...")
    try:
        start_time = time.time()
        summary = llm_service.brief_summary_of_conversation_history(
            messages=messages,
            max_tokens=500,
            temperature=0.3
        )
        end_time = time.time()
        
        print(f"\nSummary (generated in {end_time - start_time:.2f} seconds):")
        print("-" * 40)
        print(summary)
        print("\n")
        return True
    
    except Exception as e:
        print(f"\nError generating summary: {e}")
        return False


def demo_simple_conversation():
    """Demonstrate summarization with a simple conversation."""
    messages = [
        {"role": "user", "content": "What's the weather like today?"},
        {"role": "assistant", "content": "I don't have access to real-time weather data. To get the current weather, you could check a weather app, website, or look outside."},
        {"role": "user", "content": "Can you recommend some good weather apps?"},
        {"role": "assistant", "content": "Sure! Here are some popular weather apps:\n1. AccuWeather\n2. The Weather Channel\n3. Weather Underground\n4. Dark Sky\n5. Weather.com\n6. WeatherBug\nThese apps provide forecasts, radar, and other weather information."},
        {"role": "user", "content": "Thanks! I'll try AccuWeather."},
        {"role": "assistant", "content": "You're welcome! AccuWeather is a good choice. It provides detailed forecasts, radar maps, and severe weather alerts. Let me know if you need any other recommendations!"}
    ]
    
    return display_summary("SIMPLE CONVERSATION SUMMARY", messages)


def demo_media_conversation():
    """Demonstrate summarization with a conversation containing media references."""
    messages = [
        {"role": "user", "content": "Can you tell me about this diagram? ![Neural Network](https://example.com/neural_network.png)"},
        {"role": "assistant", "content": "This appears to be a diagram of a neural network architecture. Neural networks are computational models inspired by the human brain. They consist of layers of interconnected nodes or 'neurons' that process information."},
        {"role": "user", "content": "Here's another image: <img src='https://example.com/cnn.jpg' alt='CNN Architecture'>. What's the difference between this and the previous one?"},
        {"role": "assistant", "content": "The second image shows a Convolutional Neural Network (CNN) architecture, which is specialized for processing grid-like data such as images. The main difference from the standard neural network in the first image is that CNNs use convolutional layers that apply filters to detect features at different positions in the input."},
        {"role": "user", "content": "I also have this PDF about transformers: [attachment:transformers.pdf]"},
        {"role": "assistant", "content": "I see you've attached a PDF about transformers. Transformers are a type of neural network architecture introduced in the paper 'Attention Is All You Need' by Vaswani et al. They rely on a mechanism called self-attention to process sequential data without using recurrence or convolution. Transformers have revolutionized natural language processing and are the foundation of models like BERT, GPT, and T5."}
    ]
    
    return display_summary("MEDIA-RICH CONVERSATION SUMMARY", messages)


def demo_technical_conversation():
    """Demonstrate summarization with a technical conversation."""
    messages = [
        {"role": "user", "content": "What's the difference between REST and GraphQL APIs?"},
        {"role": "assistant", "content": "REST and GraphQL are two different approaches to building APIs:\n\n**REST (Representational State Transfer):**\n- Uses standard HTTP methods (GET, POST, PUT, DELETE)\n- Typically has multiple endpoints for different resources\n- Client receives fixed data structures determined by the server\n- May require multiple requests to gather related data\n- Simpler to implement and understand\n- Better caching capabilities\n\n**GraphQL:**\n- Uses a single endpoint for all operations\n- Clients specify exactly what data they need\n- Reduces over-fetching and under-fetching of data\n- Can retrieve multiple related resources in a single request\n- More complex to implement on the server side\n- Requires a schema that defines available data and operations\n\nThe choice between REST and GraphQL depends on your specific use case, client needs, and development preferences."},
        {"role": "user", "content": "When would you recommend using GraphQL over REST?"},
        {"role": "assistant", "content": "I'd recommend using GraphQL over REST in these scenarios:\n\n1. **Complex data requirements**: When clients need to fetch data from multiple related resources in a single request\n\n2. **Diverse client needs**: When different clients (web, mobile, desktop) need different data shapes from the same API\n\n3. **Rapid frontend development**: When UI requirements change frequently and you need flexibility without modifying backend endpoints\n\n4. **Bandwidth constraints**: When optimizing for limited network bandwidth is important (mobile apps)\n\n5. **Microservices architecture**: When aggregating data from multiple microservices into a unified API\n\n6. **Analytics and dashboards**: When building applications that need to query and visualize data in various ways\n\n7. **Reducing round trips**: When you want to minimize the number of HTTP requests\n\nHowever, REST might still be better for simpler APIs, when caching is critical, or when you need to leverage the HTTP protocol's features more directly."},
        {"role": "user", "content": "Are there any performance concerns with GraphQL?"},
        {"role": "assistant", "content": "Yes, there are several performance concerns with GraphQL:\n\n1. **N+1 Query Problem**: Without proper optimization, GraphQL can generate many database queries for nested resources\n\n2. **Complex Queries**: Clients can request deeply nested data or overly complex queries that strain server resources\n\n3. **Query Depth/Complexity**: Without limits, malicious or poorly designed queries can cause DoS-like situations\n\n4. **Caching Challenges**: GraphQL typically uses a single endpoint, making HTTP-level caching more difficult than REST\n\n5. **Over-fetching at the Database Level**: While GraphQL prevents over-fetching to clients, it might still over-fetch from databases\n\n6. **File Uploads**: Handling file uploads is less straightforward than with REST\n\n7. **Learning Curve**: Development teams might take longer to implement efficient resolvers\n\nThese concerns can be addressed with:\n- DataLoader pattern for batching and caching\n- Query complexity analysis\n- Persisted queries\n- Apollo Server's APQ (Automatic Persisted Queries)\n- Query depth limits\n- Timeout policies\n- Server-side caching strategies"}
    ]
    
    return display_summary("TECHNICAL CONVERSATION SUMMARY", messages)


def demo_compare_models():
    """Generate a summary of a blockchain conversation."""
    messages = [
        {"role": "user", "content": "Can you explain the concept of blockchain in simple terms?"},
        {"role": "assistant", "content": "Sure! Blockchain is like a digital ledger or record book that's shared across many computers instead of being stored in one place. Here's what makes it special:\n\n1. **Distributed**: Copies exist on many computers (nodes) in a network, not just one central server\n\n2. **Transparent**: Everyone in the network can see the same information\n\n3. **Immutable**: Once information is added, it's extremely difficult to change or delete\n\n4. **Secure**: Uses cryptography (complex math) to protect the data\n\nHere's how it works in simple steps:\n\n1. Someone requests a transaction (like sending money or recording information)\n2. This request is broadcast to the network of computers\n3. The computers validate the transaction using agreed-upon rules\n4. Verified transactions are combined with others to create a new \"block\" of data\n5. This block is added to the existing \"chain\" of blocks (hence \"blockchain\")\n6. The transaction is complete and becomes permanent\n\nIt's like writing in pen in a notebook that everyone can see, and then making photocopies for everyone to keep. If someone tries to change their copy, everyone else can see that it doesn't match theirs.\n\nBlockchain is the technology behind cryptocurrencies like Bitcoin, but it has many other potential uses like supply chain tracking, voting systems, and digital identity verification."},
        {"role": "user", "content": "What are some real-world applications besides cryptocurrency?"},
        {"role": "assistant", "content": "Blockchain has many real-world applications beyond cryptocurrency. Here are some notable examples:\n\n1. **Supply Chain Management**\n   - Tracking products from manufacturer to consumer\n   - Verifying authenticity of luxury goods or pharmaceuticals\n   - Examples: IBM Food Trust, VeChain, Walmart's food safety tracking\n\n2. **Healthcare**\n   - Secure sharing of patient records between providers\n   - Tracking pharmaceutical supply chains to prevent counterfeiting\n   - Managing healthcare data consent and access\n   - Examples: MedRec, Patientory, BurstIQ\n\n3. **Voting Systems**\n   - Creating tamper-proof voting records\n   - Increasing transparency while maintaining voter privacy\n   - Examples: Voatz, Follow My Vote\n\n4. **Digital Identity**\n   - Self-sovereign identity solutions\n   - Reducing identity theft and fraud\n   - Examples: Civic, uPort, Microsoft's ION\n\n5. **Real Estate**\n   - Property title transfers and verification\n   - Fractional ownership of properties\n   - Examples: Propy, RealT\n\n6. **Intellectual Property & Content Rights**\n   - Proving ownership of creative works\n   - Managing royalty payments\n   - Examples: Mediachain (acquired by Spotify), Binded\n\n7. **Insurance**\n   - Automating claims processing through smart contracts\n   - Reducing fraud\n   - Examples: Etherisc, B3i\n\n8. **Cross-border Payments**\n   - Faster, cheaper international transfers\n   - Examples: Ripple, Stellar\n\n9. **Government & Public Records**\n   - Land registries\n   - Business licensing\n   - Examples: Georgia's land registry, Estonia's e-government initiatives\n\n10. **Energy Trading**\n    - Peer-to-peer energy trading in microgrids\n    - Examples: Power Ledger, Grid+\n\nThese applications leverage blockchain's key features: transparency, immutability, security, and decentralization to solve real-world problems where trust, verification, and secure record-keeping are important."}
    ]
    
    # Since we now always use gpt-4o-mini, just display the summary
    return display_summary("BLOCKCHAIN CONVERSATION SUMMARY", messages)


def main():
    """Main function to run the demo."""
    parser = argparse.ArgumentParser(description="Demonstrate conversation summarization")
    parser.add_argument("demo_type", choices=["simple", "media", "technical", "compare"],
                        help="Which type of demo to run")
    
    args = parser.parse_args()
    
    if args.demo_type == "simple":
        demo_simple_conversation()
    elif args.demo_type == "media":
        demo_media_conversation()
    elif args.demo_type == "technical":
        demo_technical_conversation()
    elif args.demo_type == "compare":
        demo_compare_models()


if __name__ == "__main__":
    main()
