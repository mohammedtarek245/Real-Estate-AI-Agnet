"""
Reasoning module for the Arabic Real Estate AI Agent.
Implements chain-of-thought reasoning to make decisions based on the conversation.
"""

import logging
import re
from typing import Dict, List, Optional

from config import ConversationPhase, DEBUG
from utils.text_processing import (
    extract_entities,
    extract_preferences,  # ✅ for structured preference extraction
    analyze_intent,
    analyze_sentiment
)

# Configure logging
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

class Reasoning:
    def __init__(self):
        logger.info("Initializing reasoning module...")
        self.phase_transition_rules = self._init_phase_transition_rules()

    def _init_phase_transition_rules(self) -> Dict:
        return {
            ConversationPhase.DISCOVERY: {
                'conditions': [
                    {'type': 'information_complete', 'fields': ['location', 'budget', 'property_type']},
                    {'type': 'message_count', 'min_count': 1}
                ],
                'next_phase': ConversationPhase.SUMMARY
            },
            ConversationPhase.SUMMARY: {
                'conditions': [
                    {'type': 'confirmation', 'keywords': ['نعم', 'صحيح', 'موافق', 'تمام']},
                ],
                'next_phase': ConversationPhase.SUGGESTION
            },
            ConversationPhase.SUGGESTION: {
                'conditions': [
                    {'type': 'property_selection', 'keywords': ['أعجبني', 'مهتم', 'رائع', 'جيد']},
                ],
                'next_phase': ConversationPhase.PERSUASION
            },
            ConversationPhase.PERSUASION: {
                'conditions': [
                    {'type': 'objection', 'keywords': ['لكن', 'مشكلة', 'قلق', 'لا أحب', 'غالي']},
                ],
                'next_phase': ConversationPhase.ALTERNATIVE
            },
            ConversationPhase.ALTERNATIVE: {
                'conditions': [
                    {'type': 'interest', 'keywords': ['مهتم', 'جيد', 'أفضل', 'يعجبني']},
                ],
                'next_phase': ConversationPhase.URGENCY
            },
            ConversationPhase.URGENCY: {
                'conditions': [
                    {'type': 'intent_to_proceed', 'keywords': ['أريد', 'الآن', 'متى', 'كيف', 'إجراءات']},
                ],
                'next_phase': ConversationPhase.CLOSING
            },
            ConversationPhase.CLOSING: {
                'conditions': [
                    {'type': 'information_provided', 'fields': ['contact_name', 'phone_number']},
                ],
                'next_phase': None
            }
        }

    def analyze(self, message: str, current_phase: ConversationPhase,
                conversation_history: List[Dict], relevant_knowledge: Dict, context: Dict) -> Dict:
        logger.debug(f"Analyzing message in phase {current_phase.name}")

        # Fallback: user wants to go back
        if message.strip() in ["ارجع", "ارجع خطوة", "رجعني", "عودة"]:
            prev_phase = self._get_previous_phase(current_phase)
            logger.info(f"⚠️ User requested fallback to: {prev_phase}")
            return {
                'reasoning': f"⚠️ المستخدم طلب الرجوع للمرحلة السابقة: {prev_phase.name}",
                'extracted_info': {},
                'intent': 'fallback',
                'sentiment': 'neutral',
                'should_change_phase': True,
                'next_phase': prev_phase,
                'relevant_knowledge': {}
            }

        # Fallback: user is confused
        if message.strip() in ["مش فاهم", "مش واضح", "غلط", "مش مفهوم"]:
            logger.info("⚠️ User seems confused. Staying in current phase.")
            return {
                'reasoning': "⚠️ المستخدم غير واضح أو لديه اعتراض. نعيد المحاولة.",
                'extracted_info': {},
                'intent': 'confused',
                'sentiment': 'neutral',
                'should_change_phase': False,
                'next_phase': current_phase,
                'relevant_knowledge': {}
            }

        extracted_info = self._extract_information(message, current_phase)
        intent = analyze_intent(message)
        sentiment = analyze_sentiment(message)

        should_change_phase, next_phase = self._check_phase_transition(
            current_phase, message, extracted_info, conversation_history, context
        )

        reasoning = self._generate_reasoning(
            message, current_phase, extracted_info, intent, sentiment, should_change_phase, next_phase
        )

        return {
            'reasoning': reasoning,
            'extracted_info': extracted_info,
            'intent': intent,
            'sentiment': sentiment,
            'should_change_phase': should_change_phase,
            'next_phase': next_phase,
            'relevant_knowledge': {}
        }

    def run(self, message: str, current_phase: ConversationPhase, history: List[Dict],
            knowledge: Dict = {}, context: Dict = {}) -> Dict:
        return self.analyze(message, current_phase, history, knowledge, context)

    def _extract_information(self, message: str, current_phase: ConversationPhase) -> Dict:
        extracted_info = {}
        entities = extract_entities(message)

        if current_phase == ConversationPhase.DISCOVERY:
            # ✅ Use structured preference extractor
            extracted_info = extract_preferences(message)

        elif current_phase == ConversationPhase.CLOSING:
            if 'PERSON' in entities:
                extracted_info['contact_name'] = entities['PERSON']
            phone_match = re.findall(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', message)
            if phone_match:
                extracted_info['phone_number'] = ''.join(phone_match[0])
            email_match = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)
            if email_match:
                extracted_info['email'] = email_match[0]

        logger.debug(f"Extracted info: {extracted_info}")
        return extracted_info

    def _check_phase_transition(self, current_phase: ConversationPhase, message: str,
                                extracted_info: Dict, conversation_history: List[Dict],
                                context: Dict) -> tuple:
        rules = self.phase_transition_rules.get(current_phase, {})
        if not rules:
            return False, None

        all_met = True
        for condition in rules.get('conditions', []):
            ctype = condition['type']

            if ctype == 'information_complete':
                fields = condition['fields']
                combined = {**context.get('user_info', {}), **extracted_info}
                if not all(f in combined and combined[f] for f in fields):
                    all_met = False
                    break

            elif ctype == 'message_count':
                if len(conversation_history) < condition.get('min_count', 1) * 2:
                    all_met = False
                    break

            elif ctype in ['confirmation', 'property_selection', 'objection', 'interest', 'intent_to_proceed']:
                if not any(keyword in message.lower() for keyword in condition['keywords']):
                    all_met = False
                    break

            elif ctype == 'information_provided':
                if not all(f in extracted_info and extracted_info[f] for f in condition['fields']):
                    all_met = False
                    break

        if all_met and rules.get('next_phase') != current_phase:
            return True, rules.get('next_phase')
        return False, None

    def _generate_reasoning(self, message: str, current_phase: ConversationPhase, extracted_info: Dict,
                            intent: str, sentiment: str, should_change_phase: bool,
                            next_phase: Optional[ConversationPhase]) -> str:
        parts = [
            f"🧠 المرحلة الحالية: {current_phase.name}",
            f"🎯 القصد: {intent}",
            f"😊 المشاعر: {sentiment}"
        ]

        if extracted_info:
            parts.append("📌 المعلومات المستخرجة:")
            for key, value in extracted_info.items():
                parts.append(f"- {key}: {value}")
        else:
            parts.append("⚠️ لا توجد معلومات واضحة مستخرجة.")

        if should_change_phase and next_phase:
            parts.append(f"➡️ الانتقال للمرحلة التالية: {next_phase.name}")
        else:
            parts.append("🔁 البقاء في المرحلة الحالية.")

        return "\n".join(parts)

    def _get_previous_phase(self, current_phase: ConversationPhase) -> ConversationPhase:
        """Return the previous phase in sequence."""
        phase_list = list(ConversationPhase)
        current_idx = phase_list.index(current_phase)
        return phase_list[max(0, current_idx - 1)]
