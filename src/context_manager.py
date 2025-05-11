"""
Kontekstmanager for Jarvis Lite.
Håndterer samtalehistorik, aktiv kontekst og forventede svar.
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Håndterer samtalekontekst for Jarvis
    
    - Gemmer historik af bruger/assistent interaktioner
    - Følger aktiv kontekst (fx om vi venter på et ja/nej svar)
    - Mulighed for at tagge samtaler med metadata (fx intent)
    - Persistent lagring af kontekst til JSON
    """
    
    def __init__(self, context_file: str = "data/context.json"):
        """
        Initialiserer kontekstmanageren
        
        Args:
            context_file: Sti til JSON-fil til lagring af kontekst
        """
        self.context_file = context_file
        self.current_context: Dict[str, Any] = {
            "conversation_history": [],
            "active_context": None,
            "expected_response": None,
            "session_start": time.time(),
            "last_interaction": time.time()
        }
        self._load_context()
    
    def _load_context(self) -> None:
        """Indlæser kontekst fra fil"""
        if os.path.exists(self.context_file):
            try:
                with open(self.context_file, "r", encoding="utf-8") as f:
                    self.current_context = json.load(f)
                logger.info(f"Kontekst indlæst fra {self.context_file}")
            except Exception as e:
                logger.error(f"Fejl ved indlæsning af kontekst: {e}")
    
    def _save_context(self) -> None:
        """Gemmer kontekst til fil"""
        try:
            os.makedirs(os.path.dirname(self.context_file), exist_ok=True)
            with open(self.context_file, "w", encoding="utf-8") as f:
                json.dump(self.current_context, f, ensure_ascii=False, indent=2)
            logger.debug(f"Kontekst gemt til {self.context_file}")
        except Exception as e:
            logger.error(f"Fejl ved gem af kontekst: {e}")
    
    def add_interaction(self, user_input: str, response: str, 
                        intent: Optional[str] = None, 
                        confidence: Optional[float] = None) -> None:
        """
        Tilføjer en ny interaktion til historikken
        
        Args:
            user_input: Brugerens input
            response: Jarvis' svar
            intent: Detekteret intent (hvis tilgængelig)
            confidence: Konfidens for intent-klassifikation
        """
        # Opdater tid for sidste interaktion
        current_time = time.time()
        self.current_context["last_interaction"] = current_time
        
        # Tilføj til historik
        self.current_context["conversation_history"].append({
            "user": user_input,
            "jarvis": response,
            "intent": intent,
            "confidence": confidence,
            "timestamp": current_time
        })
        
        # Begræns historik til seneste 20 samtaler
        if len(self.current_context["conversation_history"]) > 20:
            self.current_context["conversation_history"] = self.current_context["conversation_history"][-20:]
        
        # Gem ændringer
        self._save_context()
    
    def set_expected_response(self, expected_type: str, 
                             metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Sætter forventet responstype
        
        Args:
            expected_type: Type af forventet svar ('yes_no', 'confirmation', 'text', etc.)
            metadata: Yderligere information om forventningen
        """
        self.current_context["expected_response"] = {
            "type": expected_type,
            "set_at": time.time(),
            "metadata": metadata or {}
        }
        self._save_context()
    
    def is_awaiting_response(self) -> bool:
        """
        Tjekker om vi venter på en specifik type af svar
        
        Returns:
            True hvis der forventes et specifikt svar
        """
        if not self.current_context.get("expected_response"):
            return False
            
        # Tjek om forventningen er udløbet (max 30 sekunder ventetid)
        expected = self.current_context.get("expected_response", {})
        if expected and "set_at" in expected:
            time_passed = time.time() - expected["set_at"]
            if time_passed > 30:  # 30 sekunder timeout
                self.clear_expected_response()
                return False
                
        return True
    
    def get_expected_response_type(self) -> Optional[str]:
        """
        Henter forventet responstype
        
        Returns:
            Type af forventet svar eller None
        """
        if not self.is_awaiting_response():
            return None
            
        expected = self.current_context.get("expected_response", {})
        return expected.get("type")
    
    def get_expected_response_metadata(self) -> Dict[str, Any]:
        """
        Henter metadata for forventet respons
        
        Returns:
            Metadata for forventet respons eller tom dict
        """
        if not self.is_awaiting_response():
            return {}
            
        expected = self.current_context.get("expected_response", {})
        return expected.get("metadata", {})
    
    def clear_expected_response(self) -> None:
        """Nulstiller forventet respons"""
        self.current_context["expected_response"] = None
        self._save_context()
    
    def set_active_context(self, context_name: str, 
                          data: Optional[Dict[str, Any]] = None) -> None:
        """
        Sætter aktiv kontekst for samtalen
        
        Args:
            context_name: Navn på kontekst (fx 'note_taking', 'weather_lookup')
            data: Data relateret til konteksten
        """
        self.current_context["active_context"] = {
            "name": context_name,
            "data": data or {},
            "set_at": time.time()
        }
        self._save_context()
    
    def get_active_context(self) -> Optional[Dict[str, Any]]:
        """
        Henter aktiv kontekst
        
        Returns:
            Aktiv kontekst eller None
        """
        return self.current_context.get("active_context")
    
    def clear_active_context(self) -> None:
        """Nulstiller aktiv kontekst"""
        self.current_context["active_context"] = None
        self._save_context()
    
    def get_last_user_input(self) -> Optional[str]:
        """
        Henter seneste brugerinput
        
        Returns:
            Seneste brugerinput eller None
        """
        history = self.current_context.get("conversation_history", [])
        if not history:
            return None
        return history[-1].get("user")
    
    def get_last_response(self) -> Optional[str]:
        """
        Henter seneste Jarvis-svar
        
        Returns:
            Seneste Jarvis-svar eller None
        """
        history = self.current_context.get("conversation_history", [])
        if not history:
            return None
        return history[-1].get("jarvis")
    
    def get_session_age(self) -> float:
        """
        Henter alder på nuværende session i sekunder
        
        Returns:
            Antal sekunder siden session start
        """
        start_time = self.current_context.get("session_start", time.time())
        return time.time() - start_time
    
    def reset_session(self) -> None:
        """Nulstiller session (men beholder historik)"""
        # Bevar historik
        history = self.current_context.get("conversation_history", [])
        
        # Nulstil kontekst
        self.current_context = {
            "conversation_history": history,
            "active_context": None,
            "expected_response": None,
            "session_start": time.time(),
            "last_interaction": time.time()
        }
        self._save_context()
    
    def get_conversation_history(self, max_entries: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Henter samtalehistorik
        
        Args:
            max_entries: Maks antal samtaler der returneres (seneste først)
            
        Returns:
            Liste af samtaler
        """
        history = self.current_context.get("conversation_history", [])
        if max_entries is not None:
            return history[-max_entries:]
        return history 