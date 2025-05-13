from typing import Dict, List, Optional
import json
from pathlib import Path
import datetime
import logging

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, conversation_history_path: str = "data/conversations/history"):
        self.history_path = Path(conversation_history_path)
        self.history_path.mkdir(parents=True, exist_ok=True)
        self.current_conversation = []
        self.context_window = 5  # Antal tidligere beskeder at huske
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Tilføj en besked til den nuværende samtale"""
        timestamp = datetime.datetime.now().isoformat()
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        self.current_conversation.append(message)
        
    def get_conversation_context(self) -> str:
        """Generer kontekst fra tidligere beskeder"""
        context_messages = self.current_conversation[-self.context_window:]
        context = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in context_messages
        ])
        return context
    
    def generate_prompt(self, user_input: str) -> str:
        """Generer et prompt med kontekst for LLM"""
        context = self.get_conversation_context()
        
        prompt = f"""Du er Jarvis, en dansk AI-assistent. Du er venlig, hjælpsom og svarer altid på dansk.
        
Tidligere i samtalen:
{context}

Bruger: {user_input}
Jarvis:"""
        
        return prompt
    
    def save_conversation(self):
        """Gem den nuværende samtale"""
        if not self.current_conversation:
            return
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.history_path / f"conversation_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "conversation": self.current_conversation,
                "metadata": {
                    "timestamp": timestamp,
                    "messages_count": len(self.current_conversation)
                }
            }, f, ensure_ascii=False, indent=2)
            
    def load_recent_conversations(self, limit: int = 5) -> List[Dict]:
        """Indlæs de seneste samtaler for kontekst"""
        conversations = []
        
        try:
            files = sorted(self.history_path.glob("conversation_*.json"), reverse=True)
            for file in files[:limit]:
                with open(file, "r", encoding="utf-8") as f:
                    conversations.append(json.load(f))
        except Exception as e:
            logger.error(f"Fejl ved indlæsning af samtaler: {e}")
            
        return conversations
    
    def analyze_user_patterns(self) -> Dict:
        """Analyser brugerens samtalemønstre"""
        patterns = {
            "common_topics": {},
            "avg_message_length": 0,
            "preferred_times": {},
            "frequent_questions": []
        }
        
        messages = [msg for msg in self.current_conversation if msg["role"] == "user"]
        if not messages:
            return patterns
            
        # Beregn gennemsnitlig beskedlængde
        patterns["avg_message_length"] = sum(len(msg["content"]) for msg in messages) / len(messages)
        
        # Analyser tidspunkter
        for msg in messages:
            hour = datetime.datetime.fromisoformat(msg["timestamp"]).hour
            patterns["preferred_times"][hour] = patterns["preferred_times"].get(hour, 0) + 1
            
        return patterns
    
    def get_personalized_response_style(self) -> Dict:
        """Bestem personlig svarstil baseret på brugerens mønstre"""
        patterns = self.analyze_user_patterns()
        
        style = {
            "formality_level": "neutral",
            "response_length": "medium",
            "include_emojis": False,
            "technical_level": "medium"
        }
        
        # Juster stil baseret på mønstre
        if patterns["avg_message_length"] > 100:
            style["response_length"] = "long"
            style["technical_level"] = "high"
        elif patterns["avg_message_length"] < 20:
            style["response_length"] = "short"
            style["include_emojis"] = True
            
        return style
    
    def clear_current_conversation(self):
        """Ryd den nuværende samtale"""
        self.save_conversation()
        self.current_conversation = [] 