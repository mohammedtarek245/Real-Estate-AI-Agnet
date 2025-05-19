import logging
from agent import RealEstateAgent
from phase_manager import PhaseManager
from history import ConversationHistory 
from config import ConversationPhase
from reasoning import Reasoning

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Initialize shared Reasoning engine ===
reasoning_engine = Reasoning()

# === Monkey-patch missing method into RealEstateAgent ===
def process_message(self, user_message: str, state: list = []) -> tuple[str, list]:
    self.conversation_history.add_message("user", user_message)

    # Step 1: Call reasoning engine
    reasoning_result = self.reasoning_engine.run(
        message=user_message,
        current_phase=self.phase_manager.get_current_phase(),
        history=self.conversation_history.get_history(),
        context={"user_info": self.user_info}
    )

    # Step 2: Update user_info with new extracted data
    extracted_info = reasoning_result.get("extracted_info", {})
    if extracted_info:
        self.user_info.update(extracted_info)

    # Step 3: Update phase
    next_phase = reasoning_result.get("next_phase", self.phase_manager.get_current_phase())
    if next_phase != self.phase_manager.get_current_phase() and next_phase is not None:
        self.phase_manager.set_phase(next_phase)
        self.current_phase = next_phase

    # Step 4: Generate response
    response = self._generate_response(user_message, reasoning_result, {})

    self.conversation_history.add_message("assistant", response)
    return response, state


RealEstateAgent.process_message = process_message

def run_agent_cli(dialect="Egyptian"):
    # === Initialize Core Components ===
    phase_manager = PhaseManager(start_phase=ConversationPhase.DISCOVERY)
    conversation_history = ConversationHistory()
 
    # === Create Agent ===
    agent = RealEstateAgent(
        phase_manager=phase_manager,
        conversation_history=conversation_history,
        dialect=dialect
    )

    print(f"🏠 Real Estate AI Agent (Dialect: {dialect})")
    print("ابدأ بكتابة رسالتك... (اكتب 'خروج' لإنهاء المحادثة)\n")

    state = []
    while True:
        user_message = input("👤 المستخدم: ").strip()
        if user_message.lower() in ["exit", "خروج", "quit"]:
            print("👋 مع السلامة")
            break

        try:
            response, state = agent.process_message(user_message, state)
            print(f"🤖 الوكيل: {response}\n")
        except Exception as e:
            logger.error(f"Error: {e}")
            print("❌ حدث خطأ أثناء معالجة رسالتك. حاول مرة أخرى.\n")


if __name__ == "__main__":
    run_agent_cli(dialect="Egyptian")
