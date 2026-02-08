"""
Token-Based NLP Intent Classifier for SAARA ERP Chatbot
========================================================

This module implements a traditional NLP pipeline for intent classification
using tokenization, preprocessing, TF-IDF vectorization, and cosine similarity.

NLP Pipeline:
    Raw Query → Tokenization → Lowercasing → Stop Word Removal → 
    Stemming → TF-IDF Vectorization → Cosine Similarity → Intent Classification

Author: SAARA ERP Team
Version: 1.0
"""

import re
import math
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional


# ==================== TOKENIZATION ====================

class Tokenizer:
    """
    Tokenizer class that breaks text into individual tokens (words).
    Handles punctuation, special characters, and whitespace.
    """
    
    def __init__(self):
        # Pattern to match words and numbers
        self.token_pattern = re.compile(r'\b[a-zA-Z0-9]+\b')
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize input text into a list of tokens.
        
        Args:
            text: Input string to tokenize
            
        Returns:
            List of tokens (words)
            
        Example:
            >>> tokenizer = Tokenizer()
            >>> tokenizer.tokenize("What's my attendance?")
            ['What', 's', 'my', 'attendance']
        """
        if not text:
            return []
        return self.token_pattern.findall(text)


# ==================== PREPROCESSING ====================

class TextPreprocessor:
    """
    Text preprocessing pipeline including:
    - Lowercasing
    - Stop word removal
    - Stemming (Porter Stemmer implementation)
    """
    
    # Common English stop words
    STOP_WORDS = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 
        'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
        'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
        'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
        'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
        'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
        'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
        'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to',
        'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
        'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
        'will', 'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y',
        'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn',
        'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 
        'won', 'wouldn', 'please', 'tell', 'show', 'give', 'want', 'need', 'would',
        'could', 'get', 'know', 'like'
    }
    
    def __init__(self):
        self.tokenizer = Tokenizer()
    
    def lowercase(self, tokens: List[str]) -> List[str]:
        """Convert all tokens to lowercase."""
        return [token.lower() for token in tokens]
    
    def remove_stop_words(self, tokens: List[str]) -> List[str]:
        """Remove common stop words from token list."""
        return [token for token in tokens if token not in self.STOP_WORDS]
    
    def stem(self, word: str) -> str:
        """
        Simple Porter Stemmer implementation.
        Reduces words to their root form.
        
        Examples:
            'running' → 'run'
            'attendance' → 'attend'
            'assignments' → 'assign'
        """
        # Suffix rules for stemming
        suffixes = [
            ('ational', 'ate'), ('tional', 'tion'), ('enci', 'ence'),
            ('anci', 'ance'), ('izer', 'ize'), ('isation', 'ize'),
            ('ization', 'ize'), ('ation', 'ate'), ('ator', 'ate'),
            ('alism', 'al'), ('iveness', 'ive'), ('fulness', 'ful'),
            ('ousness', 'ous'), ('aliti', 'al'), ('iviti', 'ive'),
            ('biliti', 'ble'), ('alli', 'al'), ('entli', 'ent'),
            ('eli', 'e'), ('ousli', 'ous'), ('ment', ''),
            ('ness', ''), ('ing', ''), ('ings', ''), ('ed', ''),
            ('es', ''), ('s', ''), ('ly', ''), ('ies', 'y'),
            ('ance', ''), ('ence', '')
        ]
        
        word = word.lower()
        
        for suffix, replacement in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)] + replacement
        
        return word
    
    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """Apply stemming to all tokens."""
        return [self.stem(token) for token in tokens]
    
    def preprocess(self, text: str) -> List[str]:
        """
        Full preprocessing pipeline.
        
        Pipeline:
            Text → Tokenize → Lowercase → Remove Stop Words → Stem
            
        Args:
            text: Raw input text
            
        Returns:
            List of preprocessed tokens
        """
        tokens = self.tokenizer.tokenize(text)
        tokens = self.lowercase(tokens)
        tokens = self.remove_stop_words(tokens)
        tokens = self.stem_tokens(tokens)
        return tokens


# ==================== TF-IDF VECTORIZER ====================

class TFIDFVectorizer:
    """
    TF-IDF (Term Frequency - Inverse Document Frequency) Vectorizer.
    
    Converts text documents into numerical vectors for similarity computation.
    
    TF(t,d) = (Number of times term t appears in document d) / (Total terms in d)
    IDF(t) = log(Total documents / Documents containing term t)
    TF-IDF(t,d) = TF(t,d) × IDF(t)
    """
    
    def __init__(self):
        self.vocabulary = {}  # term -> index mapping
        self.idf_values = {}  # term -> IDF value
        self.documents = []   # stored documents for reference
        
    def fit(self, documents: List[List[str]]):
        """
        Fit the vectorizer on a corpus of documents.
        Builds vocabulary and computes IDF values.
        
        Args:
            documents: List of tokenized documents (list of token lists)
        """
        self.documents = documents

        all_terms = set()
        for doc in documents:
            all_terms.update(doc)
        
        self.vocabulary = {term: idx for idx, term in enumerate(sorted(all_terms))}
        num_docs = len(documents)
        doc_freq = Counter()
        
        for doc in documents:
            unique_terms = set(doc)
            for term in unique_terms:
                doc_freq[term] += 1
        
        for term, freq in doc_freq.items():
            self.idf_values[term] = math.log((num_docs + 1) / (freq + 1)) + 1
    
    def transform(self, tokens: List[str]) -> Dict[str, float]:
        """
        Transform a tokenized document into a TF-IDF vector.
        
        Args:
            tokens: List of tokens (preprocessed)
            
        Returns:
            Dictionary mapping terms to their TF-IDF weights
        """
        tf = Counter(tokens)
        total_terms = len(tokens)

        tfidf_vector = {}
        for term, count in tf.items():
            tf_value = count / total_terms if total_terms > 0 else 0
            idf_value = self.idf_values.get(term, 1.0)
            tfidf_vector[term] = tf_value * idf_value
        
        return tfidf_vector
    
    def fit_transform(self, documents: List[List[str]]) -> List[Dict[str, float]]:
        """Fit and transform in one step."""
        self.fit(documents)
        return [self.transform(doc) for doc in documents]

def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """
    Compute cosine similarity between two TF-IDF vectors.
    
    Cosine Similarity = (A · B) / (||A|| × ||B||)
    
    Args:
        vec1: First TF-IDF vector (dict)
        vec2: Second TF-IDF vector (dict)
        
    Returns:
        Similarity score between 0 and 1
    """

    all_terms = set(vec1.keys()) | set(vec2.keys())
    

    dot_product = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in all_terms)
    
    mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return dot_product / (mag1 * mag2)


class IntentClassifier:
    """
    Intent Classification using TF-IDF and Cosine Similarity.
    
    Training Process:
        1. Define intent patterns (example queries for each intent)
        2. Preprocess all patterns
        3. Build TF-IDF vectors for patterns
        
    Classification Process:
        1. Preprocess input query
        2. Compute TF-IDF vector
        3. Find most similar pattern using cosine similarity
        4. Return corresponding intent
    """
    INTENT_PATTERNS = {
        'attendance': [
            'what is my attendance',
            'show my attendance',
            'attendance percentage',
            'how many classes attended',
            'my attendance record',
            'attendance in subject',
            'check attendance',
            'classes attended',
            'present absent record',
            'attendance status'
        ],
        'low_attendance_students': [
            'students below attendance',
            'low attendance students',
            'attendance less than percent',
            'students under attendance',
            'defaulters list',
            'attendance shortage',
            'students with poor attendance',
            'who has low attendance',
            'attendance below threshold'
        ],
        'fees': [
            'what is my fee status',
            'fees pending',
            'payment status',
            'how much fees due',
            'fee payment',
            'tuition fees',
            'fee structure',
            'pending dues',
            'fee receipt',
            'payment history'
        ],
        'assignments': [
            'my assignments',
            'pending assignments',
            'assignment deadline',
            'homework due',
            'assignment submission',
            'submitted assignments',
            'assignment list',
            'upcoming assignments',
            'assignment status'
        ],
        'pending_submissions': [
            'who has not submitted',
            'students remaining to submit',
            'pending submissions',
            'assignment not submitted',
            'students yet to submit',
            'missing submissions',
            'who hasnt submitted'
        ],
        'results': [
            'my results',
            'exam marks',
            'my grades',
            'marks in subject',
            'exam score',
            'result percentage',
            'my performance',
            'grade card',
            'marks obtained',
            'cgpa gpa'
        ],
        'timetable': [
            'my timetable',
            'class schedule',
            'todays classes',
            'weekly schedule',
            'lecture timing',
            'when is my class',
            'schedule today',
            'class timings'
        ],
        'announcements': [
            'any announcements',
            'latest notices',
            'new announcements',
            'notice board',
            'important notices',
            'whats new',
            'recent updates',
            'college announcements'
        ],
        'academic_calendar': [
            'academic calendar',
            'exam dates',
            'holiday list',
            'when is exam',
            'semester dates',
            'vacation dates',
            'academic events',
            'exam schedule'
        ]
    }
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.vectorizer = TFIDFVectorizer()
        self.intent_vectors = {}  
        self.is_trained = False
        
    def train(self):
        """
        Train the classifier on intent patterns.
        Preprocesses all patterns and builds TF-IDF vectors.
        """
        print("=" * 60)
        print("TRAINING INTENT CLASSIFIER")
        print("=" * 60)
        
        all_documents = []
        pattern_to_intent = []
        

        for intent, patterns in self.INTENT_PATTERNS.items():
            print(f"\nProcessing intent: {intent}")
            print(f"  Number of patterns: {len(patterns)}")
            
            for pattern in patterns:
                tokens = self.preprocessor.preprocess(pattern)
                all_documents.append(tokens)
                pattern_to_intent.append(intent)
                print(f"    '{pattern}' → {tokens}")
        

        print("\n" + "-" * 40)
        print("Building TF-IDF Vocabulary...")
        self.vectorizer.fit(all_documents)
        print(f"Vocabulary size: {len(self.vectorizer.vocabulary)} terms")
        print(f"Sample terms: {list(self.vectorizer.vocabulary.keys())[:10]}...")
        

        self.intent_vectors = defaultdict(list)
        for i, doc in enumerate(all_documents):
            intent = pattern_to_intent[i]
            vector = self.vectorizer.transform(doc)
            self.intent_vectors[intent].append(vector)
        
        self.is_trained = True
        print("\n" + "=" * 60)
        print("TRAINING COMPLETE!")
        print("=" * 60)
    
    def classify(self, query: str) -> Tuple[str, float, Dict]:
        """
        Classify a user query into an intent.
        
        Args:
            query: Raw user input query
            
        Returns:
            Tuple of (intent, confidence_score, debug_info)
        """
        if not self.is_trained:
            self.train()
        
        tokens = self.preprocessor.preprocess(query)
        query_vector = self.vectorizer.transform(tokens)
        
        best_intent = 'unknown'
        best_score = 0.0
        all_scores = {}
        
        for intent, vectors in self.intent_vectors.items():
            similarities = [cosine_similarity(query_vector, vec) for vec in vectors]
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0
            max_similarity = max(similarities) if similarities else 0
            
            all_scores[intent] = {
                'avg': round(avg_similarity, 4),
                'max': round(max_similarity, 4)
            }
            
            if max_similarity > best_score:
                best_score = max_similarity
                best_intent = intent

        if best_score < 0.15:
            best_intent = 'unknown'
        
        debug_info = {
            'preprocessed_tokens': tokens,
            'query_vector': {k: round(v, 4) for k, v in query_vector.items()},
            'intent_scores': all_scores,
            'confidence': round(best_score, 4)
        }
        
        return best_intent, best_score, debug_info


class EntityExtractor:
    """
    Extract entities (subjects, dates, numbers) from queries.
    Uses rule-based pattern matching.
    """
    
    SUBJECTS = [
        'python', 'java', 'database', 'dbms', 'data structures', 
        'algorithms', 'computer networks', 'operating systems', 'os',
        'machine learning', 'ml', 'artificial intelligence', 'ai',
        'web development', 'software engineering', 'mathematics',
        'statistics', 'cloud computing', 'cyber security'
    ]
    
    def extract_subject(self, query: str) -> Optional[str]:
        """Extract subject/course name from query."""
        query_lower = query.lower()
        
        for subject in self.SUBJECTS:
            if subject in query_lower:
                return subject.title()

        patterns = [
            r'(?:in|for)\s+([a-zA-Z\s]+?)(?:\s*\?|$)',
            r'marks\s+(?:in|for)\s+([a-zA-Z\s]+)',
            r'attendance\s+(?:in|for)\s+([a-zA-Z\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip().title()
        
        return None
    
    def extract_percentage(self, query: str) -> Optional[int]:
        """Extract percentage threshold from query."""
        patterns = [
            r'(\d+)\s*%',
            r'(\d+)\s*percent',
            r'below\s+(\d+)',
            r'less\s+than\s+(\d+)',
            r'under\s+(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def extract_entities(self, query: str) -> Dict:
        """Extract all entities from query."""
        return {
            'subject': self.extract_subject(query),
            'percentage_threshold': self.extract_percentage(query)
        }


class TokenBasedNLPProcessor:
    """
    Main NLP Processor that combines all components.
    
    Pipeline:
        Query → Preprocessing → Intent Classification → Entity Extraction → Result
    """
    
    def __init__(self):
        self.classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        
    def process(self, query: str, verbose: bool = True) -> Dict:
        """
        Process a user query through the complete NLP pipeline.
        
        Args:
            query: Raw user input
            verbose: Whether to print debug information
            
        Returns:
            Dictionary with intent, entities, and debug info
        """
        if verbose:
            print("\n" + "=" * 60)
            print("NLP PROCESSING PIPELINE")
            print("=" * 60)
            print(f"\n📝 INPUT QUERY: \"{query}\"")
        
        intent, confidence, debug_info = self.classifier.classify(query)
        
        if verbose:
            print(f"\n🔍 PREPROCESSING:")
            print(f"   Tokens: {debug_info['preprocessed_tokens']}")
            print(f"\n📊 TF-IDF VECTOR:")
            for term, weight in list(debug_info['query_vector'].items())[:5]:
                print(f"   '{term}': {weight}")
            print(f"\n🎯 INTENT CLASSIFICATION:")
            print(f"   Detected Intent: {intent.upper()}")
            print(f"   Confidence Score: {confidence:.2%}")
            print(f"\n   All Intent Scores:")
            for i, (intent_name, scores) in enumerate(debug_info['intent_scores'].items()):
                bar = "█" * int(scores['max'] * 20)
                print(f"   {intent_name:25} {scores['max']:.2f} {bar}")

        entities = self.entity_extractor.extract_entities(query)
        
        if verbose:
            print(f"\nEXTRACTED ENTITIES:")
            print(f"   Subject: {entities['subject'] or 'None'}")
            print(f"   Percentage: {entities['percentage_threshold'] or 'None'}")
        
        result = {
            'query': query,
            'intent': intent,
            'confidence': round(confidence, 4),
            'entities': entities,
            'debug': debug_info
        }
        
        if verbose:
            print("\n" + "=" * 60)
            print("PROCESSING COMPLETE")
            print("=" * 60)
        
        return result

def demo():
    """
    Demonstrate the Token-Based NLP Intent Classifier.
    """
    print("\n" + "=" * 70)
    print("   SAARA ERP - TOKEN-BASED NLP INTENT CLASSIFIER DEMO")
    print("=" * 70)
    

    processor = TokenBasedNLPProcessor()
    

    processor.classifier.train()

    test_queries = [
        "What is my attendance in Python?",
        "Show me students below 50% attendance",
        "Give me my marks in Database",
        "Which students haven't submitted assignment?",
        "What are the upcoming exams?",
        "Show latest announcements",
        "What's my fee status?",
        "Tell me my timetable for today"
    ]
    
    print("\n\n" + "=" * 70)
    print("   TESTING WITH SAMPLE QUERIES")
    print("=" * 70)
    
    results = []
    for query in test_queries:
        result = processor.process(query, verbose=False)
        results.append(result)
        print(f"\n Query: \"{query}\"")
        print(f"   → Intent: {result['intent'].upper()} (Confidence: {result['confidence']:.2%})")
        if result['entities']['subject']:
            print(f"   → Subject: {result['entities']['subject']}")
        if result['entities']['percentage_threshold']:
            print(f"   → Threshold: {result['entities']['percentage_threshold']}%")
    

    print("\n\n" + "=" * 70)
    print("   INTERACTIVE MODE")
    print("   Type your queries (or 'quit' to exit)")
    print("=" * 70)
    
    while True:
        try:
            query = input("\n You: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                print(" Goodbye!")
                break
            if query:
                processor.process(query, verbose=True)
        except KeyboardInterrupt:
            print("\n Goodbye!")
            break

if __name__ == "__main__":
    demo()
