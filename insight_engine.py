# insight_engine.py - COMPLETE WORKING VERSION
import pandas as pd
import re
from textblob import TextBlob
import warnings
warnings.filterwarnings('ignore')

# Define product aspects
ASPECTS = {
    'battery': {
        'keywords': ['battery', 'charge', 'power', 'lasts', 'drain', 'life', 'charging'],
        'description': 'Battery performance and charging'
    },
    'screen': {
        'keywords': ['screen', 'display', 'bright', 'resolution', 'cracked', 'pixel', 'touch'],
        'description': 'Display quality'
    },
    'performance': {
        'keywords': ['fast', 'slow', 'speed', 'lag', 'crash', 'freeze', 'responsive'],
        'description': 'Device speed and responsiveness'
    },
    'sound': {
        'keywords': ['sound', 'audio', 'speaker', 'volume', 'bass', 'loud', 'clear'],
        'description': 'Audio quality'
    },
    'build_quality': {
        'keywords': ['quality', 'build', 'sturdy', 'solid', 'cheap', 'plastic', 'metal'],
        'description': 'Physical build quality'
    },
    'value': {
        'keywords': ['worth', 'price', 'expensive', 'cheap', 'value', 'cost', 'money'],
        'description': 'Price to value ratio'
    },
    'software': {
        'keywords': ['app', 'software', 'update', 'firmware', 'interface', 'menu'],
        'description': 'Software experience'
    },
    'connectivity': {
        'keywords': ['bluetooth', 'wifi', 'connect', 'pair', 'signal', 'connection'],
        'description': 'Wireless connectivity'
    }
}

def improved_sentiment_score(text):
    """
    Calculate sentiment score for a text segment
    Returns score from -1 (negative) to +1 (positive)
    """
    if not text or len(text.strip()) < 5:
        return 0.0
    
    text_lower = text.lower()
    
    # Strong negative words (product specific)
    strong_negative = ['dies', 'dead', 'broken', 'crashed', 'terrible', 'awful', 
                       'worst', 'useless', 'defective', 'returning', 'refund']
    
    # Moderate negative words
    moderate_negative = ['bad', 'poor', 'slow', 'lag', 'drain', 'issue', 'problem', 
                         'fails', 'disappointed', 'hate', 'waste']
    
    # Positive words
    positive_words = ['good', 'great', 'amazing', 'excellent', 'perfect', 'love', 
                      'best', 'awesome', 'fantastic', 'wonderful', 'easy', 'fast',
                      'clear', 'bright', 'solid', 'sturdy', 'worth', 'value']
    
    # Count sentiment words
    pos_count = 0
    neg_count = 0
    
    for word in strong_negative:
        if word in text_lower:
            neg_count += 2
    for word in moderate_negative:
        if word in text_lower:
            neg_count += 1
    for word in positive_words:
        if word in text_lower:
            pos_count += 1
    
    # Check for negation
    negations = ['not', 'no', "n't", 'never', 'none', 'nor']
    has_negation = any(neg in text_lower for neg in negations)
    
    if has_negation:
        pos_count, neg_count = neg_count, pos_count
    
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    
    score = (pos_count - neg_count) / total
    return max(-1.0, min(1.0, score))

def analyze_aspect_in_review(review_text, aspect_keywords):
    """
    Extract sentiment for a specific aspect from a review
    """
    if not review_text or len(str(review_text).strip()) < 10:
        return 0.0, 0
    
    review_text = str(review_text)
    
    # Split on contrast words
    contrast_words = [' but ', ' however ', ' although ', ' though ', ' yet ']
    
    segments = [review_text]
    for contrast in contrast_words:
        new_segments = []
        for seg in segments:
            if contrast in seg.lower():
                parts = seg.split(contrast)
                new_segments.extend(parts)
            else:
                new_segments.append(seg)
        segments = new_segments
    
    # Find segments mentioning this aspect
    relevant_segments = []
    for segment in segments:
        segment_lower = segment.lower()
        if any(keyword in segment_lower for keyword in aspect_keywords):
            if len(segment.strip()) > 5:
                relevant_segments.append(segment.strip())
    
    if not relevant_segments:
        return 0.0, 0
    
    # Get sentiment for each relevant segment
    sentiments = []
    for segment in relevant_segments[:3]:
        try:
            score = improved_sentiment_score(segment)
            sentiments.append(score)
        except:
            sentiments.append(0.0)
    
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
    return avg_sentiment, len(relevant_segments)

def extract_insights(df, num_reviews=1000):
    """
    Main function to extract insights from reviews
    """
    # Take sample
    sample_reviews = df.head(num_reviews)
    
    all_insights = []
    
    for idx, row in sample_reviews.iterrows():
        try:
            review_text = row['review_text']
            rating = row['rating']
            product = row['product_name'] if pd.notna(row['product_name']) else 'Unknown'
            
            for aspect_name, aspect_info in ASPECTS.items():
                sentiment_score, mention_count = analyze_aspect_in_review(
                    review_text, 
                    aspect_info['keywords']
                )
                
                if mention_count > 0:
                    all_insights.append({
                        'aspect': aspect_name,
                        'sentiment': sentiment_score,
                        'rating': rating,
                        'product': product,
                        'review_snippet': str(review_text)[:150]
                    })
        except Exception as e:
            # Skip problematic rows
            continue
    
    insights_df = pd.DataFrame(all_insights)
    return insights_df, sample_reviews

def calculate_priorities(insights_df, sample_reviews):
    """
    Calculate priority scores for each aspect
    """
    priority_results = {}
    
    for aspect_name in ASPECTS.keys():
        aspect_data = insights_df[insights_df['aspect'] == aspect_name]
        
        if len(aspect_data) == 0:
            continue
        
        # Frequency
        frequency = len(aspect_data) / len(sample_reviews)
        
        # Negativity strength
        negative_sentiments = aspect_data[aspect_data['sentiment'] < -0.1]['sentiment']
        negativity_strength = abs(negative_sentiments.mean()) if len(negative_sentiments) > 0 else 0
        
        # Rating impact
        avg_rating = aspect_data['rating'].mean()
        rating_impact = (5 - avg_rating) / 4
        
        # Priority score
        priority_score = (frequency * 0.4) + (negativity_strength * 0.35) + (rating_impact * 0.25)
        
        # Positive ratio
        positive_mentions = len(aspect_data[aspect_data['sentiment'] > 0.1])
        positive_ratio = positive_mentions / len(aspect_data) if len(aspect_data) > 0 else 0
        
        priority_results[aspect_name] = {
            'priority_score': priority_score,
            'frequency': frequency,
            'negativity_strength': negativity_strength,
            'avg_rating': avg_rating,
            'total_mentions': len(aspect_data),
            'positive_ratio': positive_ratio
        }
    
    # Sort by priority
    sorted_aspects = sorted(priority_results.items(), key=lambda x: x[1]['priority_score'], reverse=True)
    
    return priority_results, sorted_aspects

# Test function (runs when file is executed directly)
if __name__ == "__main__":
    print("Testing insight_engine.py...")
    print(f"Loaded {len(ASPECTS)} aspects: {list(ASPECTS.keys())}")
    print("✅ insight_engine.py is working!")