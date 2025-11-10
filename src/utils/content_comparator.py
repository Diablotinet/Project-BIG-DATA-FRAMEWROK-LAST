"""
Content Comparator - Analyse comparative AFP vs autres sources
Utilise l'IA pour détecter déformation et objectivité
"""

import logging
from typing import Dict, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob
from transformers import pipeline
import re

logging.basicConfig(level=logging.INFO)

class ContentComparator:
    """Comparateur de contenu avec analyse IA"""
    
    def __init__(self):
        self.logger = logging.getLogger("ContentComparator")
        self.vectorizer = TfidfVectorizer(max_features=1000)
        
        # Charger modèle de sentiment Hugging Face
        try:
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment"
            )
            self.logger.info("✅ Modèle IA chargé")
        except Exception as e:
            self.logger.warning(f"⚠️ Modèle IA non chargé: {e}")
            self.sentiment_analyzer = None
    
    def compute_content_similarity(self, afp_content: str, other_content: str) -> float:
        """Calcule la similarité de contenu entre AFP et autre source"""
        try:
            # Vectorisation TF-IDF
            vectors = self.vectorizer.fit_transform([afp_content, other_content])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            self.logger.error(f"Erreur similarité: {e}")
            return 0.0
    
    def detect_bias(self, afp_content: str, other_content: str) -> Dict:
        """Détecte le biais entre AFP (référence) et autre source"""
        
        # Analyse de sentiment AFP (référence objective)
        afp_sentiment = TextBlob(afp_content).sentiment.polarity
        
        # Analyse de sentiment autre source
        other_sentiment = TextBlob(other_content).sentiment.polarity
        
        # Différence de sentiment = indicateur de biais
        sentiment_diff = abs(afp_sentiment - other_sentiment)
        
        # Analyse lexicale
        afp_words = set(re.findall(r'\b\w+\b', afp_content.lower()))
        other_words = set(re.findall(r'\b\w+\b', other_content.lower()))
        
        # Mots ajoutés (potentiellement biaisés)
        added_words = other_words - afp_words
        
        # Mots émotionnels
        emotional_words = self._detect_emotional_words(added_words)
        
        # Score de déformation (0-1)
        deformation_score = min(1.0, (
            sentiment_diff * 0.4 +  # Différence de sentiment
            (len(emotional_words) / max(1, len(added_words))) * 0.3 +  # Mots émotionnels
            (1 - self.compute_content_similarity(afp_content, other_content)) * 0.3
        ))
        
        return {
            'deformation_score': deformation_score,
            'sentiment_difference': sentiment_diff,
            'afp_sentiment': afp_sentiment,
            'other_sentiment': other_sentiment,
            'emotional_words_count': len(emotional_words),
            'emotional_words': list(emotional_words)[:10],
            'objectivity_score': 1 - deformation_score,
            'interpretation': self._interpret_deformation(deformation_score)
        }
    
    def _detect_emotional_words(self, words: set) -> set:
        """Détecte les mots émotionnels/sensationnels"""
        emotional_lexicon = {
            'shocking', 'terrible', 'amazing', 'incredible', 'unbelievable',
            'scandalous', 'outrageous', 'fantastic', 'horrible', 'awesome',
            'choquant', 'terrible', 'incroyable', 'scandaleux', 'fantastique',
            'horrible', 'extraordinaire', 'catastrophique', 'merveilleux'
        }
        return words & emotional_lexicon
    
    def _interpret_deformation(self, score: float) -> str:
        """Interprète le score de déformation"""
        if score < 0.2:
            return "Très objectif - Peu de déformation"
        elif score < 0.4:
            return "Objectif - Légère déformation"
        elif score < 0.6:
            return "Modérément biaisé - Déformation notable"
        elif score < 0.8:
            return "Biaisé - Forte déformation"
        else:
            return "Très biaisé - Déformation majeure"
    
    def compare_articles(self, afp_article: Dict, other_articles: List[Dict]) -> List[Dict]:
        """Compare un article AFP avec plusieurs autres sources"""
        results = []
        
        afp_content = afp_article.get('content', '')
        
        for article in other_articles:
            other_content = article.get('content', '')
            
            # Similarité de contenu
            similarity = self.compute_content_similarity(afp_content, other_content)
            
            # Analyse de biais
            bias_analysis = self.detect_bias(afp_content, other_content)
            
            # Délai de publication
            afp_time = afp_article.get('timestamp')
            other_time = article.get('timestamp')
            time_delay = self._calculate_time_delay(afp_time, other_time)
            
            results.append({
                'source': article.get('source'),
                'source_type': article.get('source_type'),
                'content_similarity': similarity,
                **bias_analysis,
                'time_delay_hours': time_delay,
                'match_quality': self._calculate_match_quality(similarity, bias_analysis)
            })
        
        return sorted(results, key=lambda x: x['match_quality'], reverse=True)
    
    def _calculate_time_delay(self, afp_time: str, other_time: str) -> float:
        """Calcule le délai entre AFP et autre source (en heures)"""
        from datetime import datetime
        
        try:
            afp_dt = datetime.fromisoformat(afp_time.replace('Z', '+00:00'))
            other_dt = datetime.fromisoformat(other_time.replace('Z', '+00:00'))
            delay = (other_dt - afp_dt).total_seconds() / 3600
            return delay
        except:
            return 0.0
    
    def _calculate_match_quality(self, similarity: float, bias_analysis: Dict) -> float:
        """Calcule la qualité du match (0-1)"""
        return (
            similarity * 0.5 +  # Similarité de contenu
            bias_analysis['objectivity_score'] * 0.3 +  # Objectivité
            (1 - min(1.0, abs(bias_analysis['sentiment_difference']))) * 0.2
        )
