import logging
from typing import List, Dict, Tuple
import re
import os
import json

from config import ConversationPhase
from phase_manager import PhaseManager
from history import ConversationHistory
from reasoning import Reasoning
from knowledge.knowledge_base import KnowledgeBase
from knowledge.retrieval import KnowledgeRetrieval

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealEstateAgent:
    def __init__(self, phase_manager: PhaseManager, conversation_history: ConversationHistory,
                 primary_model=None, fallback_model=None, dialect="Egyptian"):
        self.phase_manager = phase_manager
        self.conversation_history = conversation_history
        self.dialect = dialect
        self.reasoning_engine = Reasoning()
        self.user_info = {}
        self.context = {}
        self.selected_properties = []
        self.last_mentioned_property = None

        self.current_phase = self.phase_manager.get_current_phase() or ConversationPhase.DISCOVERY
        self.asked_questions = set()

        self.knowledge_base = KnowledgeBase()
        self.knowledge_retriever = KnowledgeRetrieval(self.knowledge_base)

        # ✅ Load rule-based reasoning knowledge
        self.rules = self._load_rules()

    def _load_rules(self):
        rules_path = os.path.join("knowledge", "rules.json")
        if os.path.exists(rules_path):
            with open(rules_path, encoding="utf-8") as f:
                return json.load(f)
        else:
            logger.warning("rules.json not found.")
            return {}

    def process_message(self, user_message: str, state: list = []) -> Tuple[str, list]:
        self.conversation_history.add_user_message(user_message)

        logger.info(f"📩 Received message: {user_message}")
        logger.info(f"🔄 Current phase: {self.current_phase}")
        logger.info(f"📌 User info before reasoning: {self.user_info}")

        self._basic_info_extraction(user_message)

        relevant_knowledge = self.knowledge_retriever.retrieve(
            query=user_message,
            phase=self.current_phase,
            context={"user_info": self.user_info}
        )

        reasoning_result = self.reasoning_engine.analyze(
            message=user_message,
            current_phase=self.current_phase,
            conversation_history=self.conversation_history.get_all(),
            relevant_knowledge=relevant_knowledge,
            context={"user_info": self.user_info}
        )

        extracted_info = reasoning_result.get("extracted_info", {})
        if extracted_info:
            self.user_info.update(extracted_info)

        # ✅ Handle vague references like "هي مش عاجباني"
        if self._is_reference_to_previous_property(user_message):
            logger.info("🔎 User is referring to a previously shown property.")
            self.user_info["refers_to"] = self.last_mentioned_property or "غير واضح"

        next_phase = reasoning_result.get("next_phase", self.current_phase)
        if next_phase and next_phase != self.current_phase:
            self.current_phase = next_phase
            self.phase_manager.set_current_phase(next_phase)

        self.context["user_info"] = self.user_info

        response = self._generate_response(user_message, reasoning_result, relevant_knowledge)
        self.conversation_history.add_assistant_message(response)

        return response, state

    def _basic_info_extraction(self, message: str):
        message_lower = message.lower()
        locations = [
            "القاهرة", "الاسكندرية", "الجيزة", "المعادي", "مدينة نصر", "6 أكتوبر", "التجمع",
            "الشروق", "العبور", "الرحاب", "مدينتي", "الشيخ زايد", "المهندسين", "الدقي",
            "الزمالك", "وسط البلد", "مصر الجديدة", "حلوان"
        ]
        for location in locations:
            if location in message and "location" not in self.user_info:
                self.user_info["location"] = location
                break

        budget_pattern = r'(\d[\d,]*)\s*(جنيه|الف|مليون|k|m)'
        budget_match = re.search(budget_pattern, message)
        if budget_match and "budget" not in self.user_info:
            amount = budget_match.group(1).replace(',', '')
            unit = budget_match.group(2)
            budget = f"{amount} {'ألف جنيه' if unit in ['k', 'الف'] else 'مليون جنيه' if unit in ['m', 'مليون'] else 'جنيه'}"
            self.user_info["budget"] = budget

        property_types = {
            "شقة": ["شقة", "شقه", "apartment"],
            "فيلا": ["فيلا", "فيلات", "villa"],
            "دوبلكس": ["دوبلكس", "duplex"],
            "ستوديو": ["ستوديو", "studio"],
            "محل": ["محل", "محلات", "shop"],
            "مكتب": ["مكتب", "مكاتب", "office"]
        }
        for prop_type, keywords in property_types.items():
            for keyword in keywords:
                if keyword in message_lower and "property_type" not in self.user_info:
                    self.user_info["property_type"] = prop_type
                    break

    def _is_reference_to_previous_property(self, message: str) -> bool:
        vague_words = ['هي', 'ده', 'دي', 'العقار ده', 'العرض ده']
        reference_patterns = [rf'{word}.*(مش|ما عجبني|ما عجباني|ما عجبها|ما حبيتها)' for word in vague_words]
        return any(re.search(p, message.lower()) for p in reference_patterns)

    def _apply_rule_logic(self, user_info: dict, property_data: dict = None) -> List[str]:
        advice = []

        # Budget logic
        budget_value = user_info.get("budget", "")
        if "مليون" in budget_value:
            advice += [r["response"] for r in self.rules.get("budget_advice", []) if r["condition"] == "budget_high"]
        elif "ألف" in budget_value:
            try:
                numeric = int(re.findall(r'\d+', budget_value)[0])
                if numeric < 500:
                    advice += [r["response"] for r in self.rules.get("budget_advice", []) if r["condition"] == "budget_low"]
                else:
                    advice += [r["response"] for r in self.rules.get("budget_advice", []) if r["condition"] == "budget_mid"]
            except:
                pass

        # Feature-based advice
        features = []
        if property_data and "features" in property_data:
            features = [f.strip() for f in property_data["features"].split('،')]
        elif "features" in user_info:
            features = user_info["features"]

        for f in features:
            for rule in self.rules.get("property_priority", []):
                if rule["feature"] in f:
                    advice.append(rule["response"])

        return advice

    def _generate_response(self, user_message, reasoning_result, relevant_knowledge={}):
        phase = self.current_phase
        user_info = self.user_info

        if phase == ConversationPhase.DISCOVERY:
            return self._discovery_response(user_info, relevant_knowledge)
        elif phase == ConversationPhase.SUMMARY:
            return self._summary_response(user_info)
        elif phase == ConversationPhase.SUGGESTION:
            return self._suggest_properties(user_info, relevant_knowledge)
        elif phase == ConversationPhase.PERSUASION:
            referred = self.user_info.get("refers_to", None)
            if referred and isinstance(referred, dict):
                return f"ليه مش عاجبك؟ ده فيه {referred.get('features', 'مميزات رائعة')} وموقعه في {referred.get('location', 'مكان ممتاز')}."
            return "ممكن توضح إيه اللي مش عاجبك؟ نقدر نعرض بديل."
        elif phase == ConversationPhase.ALTERNATIVE:
            return "ممكن نعرض عليك اختيارات تانية قريبة من اللي بتحبّه."
        elif phase == ConversationPhase.URGENCY:
            return "الفرص دي مش بتستنى! تحب نكمل إجراءات المعاينة؟"
        elif phase == ConversationPhase.CLOSING:
            return "تمام، ابعتلي اسمك ورقم تليفونك وهنكلمك في أقرب وقت."
        return "أنا هنا أساعدك. تحب تبدأ بإيه؟"

    def _discovery_response(self, user_info: dict, knowledge: dict = {}) -> str:
        missing = []
        if not user_info.get("location"): missing.append("المكان")
        if not user_info.get("budget"): missing.append("الميزانية")
        if not user_info.get("property_type"): missing.append("نوع العقار")

        if missing:
            prompt = knowledge.get("phase_knowledge", {}).get("suggested_questions", [])
            extra = f"\nمثلاً: {prompt[0]}" if prompt else ""
            return f"ممكن تقولي {', '.join(missing)}؟ علشان أقدر أساعدك بشكل أفضل.{extra}"

        return "تمام! كده أنا عرفت اللي محتاجه، نراجع المعلومات؟"

    def _summary_response(self, user_info: dict) -> str:
        summary = []
        if "location" in user_info: summary.append(f"📍 الموقع: {user_info['location']}")
        if "budget" in user_info: summary.append(f"💰 الميزانية: {user_info['budget']}")
        if "property_type" in user_info:
            summary.append(f"🏠 النوع: {user_info['property_type']}")

        advice = self._apply_rule_logic(user_info)
        return "دي المعلومات اللي جمعتها:\n" + "\n".join(summary) + (
            "\n\n🧠 نصيحة:\n" + "\n".join(advice) if advice else ""
        ) + "\nهل الكلام ده مظبوط؟"

    def _suggest_properties(self, user_info: dict, knowledge: dict = {}) -> str:
        matching_properties = knowledge.get("relevant_properties", [])
        if not matching_properties:
            return "معرفتش ألاقي عقارات بالمواصفات دي، تحب نغيّر شوية في الطلب؟"

        self.selected_properties = matching_properties
        self.last_mentioned_property = self.selected_properties[0]
        reply = "🏡 العقارات دي ممكن تعجبك:\n"
        for prop in self.selected_properties:
            reply += f"- {prop['type']} في {prop['location']} بـ {prop['price']} جنيه\n"

        # 🔍 Apply expert rule logic to the first suggested property
        extra = self._apply_rule_logic(user_info, self.last_mentioned_property)
        if extra:
            reply += "\n🧠 ملاحظات:\n" + "\n".join(extra)

        reply += "\nهل في واحد منهم شد انتباهك؟"
        return reply
