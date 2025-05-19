import logging
from config import ConversationPhase

logger = logging.getLogger(__name__)

class PhaseManager:
    def __init__(
        self,
        dialect: str = "Egyptian",  # Default is Egyptian
        start_phase: ConversationPhase = ConversationPhase.DISCOVERY
    ):
        self.dialect = dialect
        self.current_phase = start_phase
        logger.info(f"PhaseManager initialized with dialect: {dialect}, starting phase: {start_phase}")

    def get_current_phase(self) -> ConversationPhase:
        return self.current_phase

    def set_current_phase(self, new_phase: ConversationPhase):
        """Set the current conversation phase manually."""
        if self.current_phase == new_phase:
            logger.info(f"Already in phase: {new_phase.name}")
            return
            
        self.current_phase = new_phase
        logger.info(f"✅ Current phase set to: {self.current_phase.name}")

    def advance_phase(self):
        if self.current_phase == ConversationPhase.CLOSING:
            logger.info("📌 Already at final phase.")
            return

        phase_order = list(ConversationPhase)
        current_index = phase_order.index(self.current_phase)
        self.current_phase = phase_order[current_index + 1]
        logger.info(f"➡️ Advanced to phase: {self.current_phase.name}")

    def set_phase(self, phase: ConversationPhase):
        """Alias for set_current_phase for legacy compatibility."""
        self.set_current_phase(phase)

    def get_system_prompt(self, phase: ConversationPhase, user_info: dict, selected_properties: list) -> str:
        """
        Generates a hard-coded Egyptian Arabic prompt based on phase and minimal user info.
        """
        logger.info(f"Generating system prompt for phase: {phase.name} with user_info: {user_info}")
        
        if phase == ConversationPhase.DISCOVERY:
            # Check what information we already have
            missing = []
            if "location" not in user_info:
                missing.append("المكان")
            if "budget" not in user_info:
                missing.append("الميزانية")
            if "property_type" not in user_info:
                missing.append("نوع العقار")
                
            if missing:
                return f"محتاج أعرف {', '.join(missing)} علشان أقدر أساعدك."
            else:
                return "قولي أي متطلبات تانية مهمة بالنسبالك في العقار."

        elif phase == ConversationPhase.SUMMARY:
            # Build a natural summary message from collected user info
            parts = []
            if "property_type" in user_info:
                parts.append(user_info["property_type"])
            if "location" in user_info:
                parts.append(f"في {user_info['location']}")
            if "budget" in user_info:
                parts.append(f"بميزانية حوالي {user_info['budget']}")

            if parts:
                summary = " ".join(parts)
                return f"فهمت إنك بتدور على {summary}. صح كده؟"
            else:
                return "حابب تأكدلي انت بتدور على إيه بالظبط؟"

        elif phase == ConversationPhase.SUGGESTION:
            return "دي شوية عقارات ممكن تناسب اللي بتدور عليه، شوفهم وقولي رأيك."

        elif phase == ConversationPhase.PERSUASION:
            return "العقار ده فيه مميزات كتير زي الموقع والمساحة. تحب أقولك أكتر ليه ممكن يكون اختيار ممتاز؟"

        elif phase == ConversationPhase.ALTERNATIVE:
            return "ممكن تبص على اختيارات تانية مشابهة لو العقار ده مش عاجبك تماماً."

        elif phase == ConversationPhase.URGENCY:
            return "العقارات دي بتروح بسرعة، لو مهتم أنصح نحجز معاينة أو تواصل فوري."

        elif phase == ConversationPhase.CLOSING:
            return "ممتاز! خلينا نبدأ في الإجراءات أو نحجزلك زيارة."

        else:
            return "أنا موجود علشان أساعدك، تحب تبدأ بإيه؟"