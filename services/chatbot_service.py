from openai import OpenAI
from typing import Dict, Any
import re
from config import Config

class ChatbotService:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.system_prompt = """
        You are a professional banking assistant. Analyze user queries and respond with:
        
        INTENT: One of [CHITCHAT, GET_BALANCE, TRANSFER_MONEY, ACCOUNT_INFO]
        
        For TRANSFER_MONEY: Extract account number and amount
        Format: TRANSFER|account_number|amount
        
        For GET_BALANCE: Extract account number if provided
        Format: BALANCE|account_number (use user's account if none specified)
        
        For ACCOUNT_INFO: General account information request
        Format: INFO
        
        For CHITCHAT: Friendly banking-related conversation
        Format: CHAT|your_response
        
        Always be professional, secure, and helpful.
        """

    def process_query(self, user_input: str, user_name: str) -> Dict[str, Any]:
        """Process user query and return structured response"""
        try:
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"User: {user_name}\nQuery: {user_input}"}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            response = completion.choices[0].message.content.strip()
            return self._parse_response(response)
            
        except Exception as e:
            return {
                "intent": "ERROR",
                "message": "I'm having trouble processing your request. Please try again.",
                "error": str(e)
            }

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI response into structured data"""
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('TRANSFER|'):
                parts = line.split('|')
                if len(parts) >= 3:
                    return {
                        "intent": "TRANSFER_MONEY",
                        "account_number": parts[1].strip(),
                        "amount": self._extract_amount(parts[2])
                    }
            
            elif line.startswith('BALANCE|'):
                parts = line.split('|')
                account = parts[1].strip() if len(parts) > 1 else None
                return {
                    "intent": "GET_BALANCE",
                    "account_number": account
                }
            
            elif line.startswith('INFO'):
                return {
                    "intent": "ACCOUNT_INFO"
                }
            
            elif line.startswith('CHAT|'):
                message = line.split('|', 1)[1] if '|' in line else "How can I help you today?"
                return {
                    "intent": "CHITCHAT",
                    "message": message
                }
        
        # Fallback parsing
        return {
            "intent": "CHITCHAT",
            "message": "I'm here to help with your banking needs. You can check balances, transfer money, or ask general questions."
        }

    def _extract_amount(self, amount_str: str) -> float:
        """Extract numeric amount from string"""
        # Remove currency symbols and extract numbers
        amount_match = re.search(r'[\d,]+\.?\d*', amount_str.replace(',', ''))
        if amount_match:
            return float(amount_match.group())
        return 0.0