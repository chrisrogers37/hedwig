"""
Integration test for DJ outreach email generation and review.

This test simulates the complete end-to-end flow:
1. User provides DJ outreach prompt
2. LLM generates email (real OpenAI call)
3. Review agent evaluates the email
4. Returns structured feedback

This is a true integration test that exercises the full system.
"""
import pytest
import os
from unittest.mock import patch
from src.services.config_service import AppConfig
from src.services.llm_service import LLMService
from src.services.prompt_builder import PromptBuilder
from src.services.profile_manager import Profile, ProfileManager
from src.services.chat_history_manager import ChatHistoryManager, MessageType
from src.services.review_agent.review_agent import ReviewAgent
from src.services.scroll_retriever import ScrollRetriever


class TestDJOutreachIntegration:
    """Integration test for DJ outreach email generation and review."""
    
    @pytest.fixture
    def app_config(self):
        """Initialize app configuration."""
        return AppConfig()
    
    @pytest.fixture
    def llm_service(self, app_config):
        """Initialize LLM service with real OpenAI integration."""
        return LLMService(app_config)
    
    @pytest.fixture
    def chat_history_manager(self):
        """Initialize chat history manager."""
        return ChatHistoryManager()
    
    @pytest.fixture
    def profile(self):
        """Initialize user profile for DJ outreach."""
        return Profile(
            name="Alex DJ",
            title="Professional DJ",
            company="SoundWave Entertainment"
        )
    
    @pytest.fixture
    def profile_manager(self, profile):
        pm = ProfileManager()
        pm.profile = profile
        return pm
    
    @pytest.fixture
    def scroll_retriever(self):
        """Initialize scroll retriever for template retrieval."""
        # Always resolve relative to project root
        scrolls_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../scrolls'))
        return ScrollRetriever(scrolls_dir)
    
    def test_dj_outreach_complete_flow(
        self,
        app_config,
        llm_service,
        chat_history_manager,
        profile_manager,
        scroll_retriever
    ):
        """
        Test the complete DJ outreach flow from prompt to reviewed email.
        
        This test:
        1. Sets up a DJ outreach scenario
        2. Generates an email using the LLM
        3. Reviews the email using the review agent
        4. Returns structured results
        """
        # Skip if no OpenAI API key (allows running without real API)
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set - skipping real LLM integration test")
        
        # Step 1: Set up the DJ outreach scenario
        user_prompt = """
        I'm a DJ in NYC looking to book a gig at Elsewhere. Please help me create an outreach email.
        """
        
        print("\n" + "="*60)
        print("🎵 DJ OUTREACH INTEGRATION TEST")
        print("="*60)
        print(f"📝 User Prompt: {user_prompt.strip()}")
        
        # Step 2: Add user prompt to chat history
        print("\n" + "─"*40)
        print("📝 STEP 1: ADDING USER PROMPT TO CHAT HISTORY")
        print("─"*40)
        chat_history_manager.add_message(user_prompt, MessageType.INITIAL_PROMPT)
        print("✅ User prompt added to chat history")
        
        # Step 3: Retrieve relevant template/guidance
        print("\n" + "─"*40)
        print("🔍 STEP 2: RETRIEVING RELEVANT TEMPLATE")
        print("─"*40)
        try:
            template_info = scroll_retriever.query(
                query_text="DJ outreach to venues",
                top_k=1,
                min_similarity=0.5  # Lower threshold for testing
            )
            print(f"📋 Retrieved template info: {len(template_info)} templates found")
            if template_info:
                template = template_info[0][0]
                print(f"📄 Template: {template.id}")
                print(f"🎯 Use Case: {template.use_case}")
                print(f"🏭 Industry: {template.industry}")
        except Exception as e:
            print(f"⚠️  Template retrieval failed: {e}")
            template_info = []
        
        # Step 4: Generate the email using LLM
        print("\n" + "─"*40)
        print("🤖 STEP 3: GENERATING EMAIL WITH LLM")
        print("─"*40)
        try:
            generated_email = PromptBuilder(llm_service, chat_history_manager, profile_manager, app_config, scroll_retriever).generate_draft()
            
            if not generated_email:
                pytest.fail("LLM failed to generate email")
            
            print(f"✅ Email generated successfully ({len(generated_email)} characters)")
            print("\n" + "📧" + "─"*38)
            print("📧 GENERATED EMAIL:")
            print("📧" + "─"*38)
            print(generated_email)
            print("📧" + "─"*38)
            
        except Exception as e:
            pytest.fail(f"Email generation failed: {e}")
        
        # Step 5: Review the generated email
        print("\n" + "─"*40)
        print("🔍 STEP 4: REVIEWING EMAIL WITH REVIEW AGENT")
        print("─"*40)
        try:
            review_result = ReviewAgent(llm_service).review_email(
                email_content=generated_email,
                template_info=template_info[0][0].metadata if template_info else None,
                user_context="DJ outreach to venue managers",
                recipient_industry="entertainment",
                extra_metadata={
                    "email_type": "cold_outreach",
                    "target_role": "venue_manager",
                    "industry": "entertainment"
                }
            )
            
            print(f"✅ Review completed successfully")
            print(f"📊 Review stats: {len(review_result.actionable_feedback)} feedback items")
            print(f"🔄 Should regenerate: {review_result.should_regenerate}")
            
        except Exception as e:
            pytest.fail(f"Review failed: {e}")
        
        # Step 6: Display structured results
        print("\n" + "─"*40)
        print("📋 STEP 5: DISPLAYING FINAL RESULTS")
        print("─"*40)
        
        print("\n" + "="*60)
        print("📋 FINAL RESULTS SUMMARY")
        print("="*60)
        
        # Original generated email
        print("\n📧 1️⃣ ORIGINAL GENERATED EMAIL:")
        print("📧" + "─" * 38)
        print(generated_email)
        print("📧" + "─" * 38)
        
        # Full feedback response
        print("\n💬 2️⃣ FULL FEEDBACK RESPONSE:")
        print("💬" + "─" * 38)
        print(review_result.critique)
        print("💬" + "─" * 38)
        
        # Structured feedback list
        print("\n✅ 3️⃣ STRUCTURED FEEDBACK LIST:")
        print("✅" + "─" * 38)
        if review_result.actionable_feedback:
            for i, feedback in enumerate(review_result.actionable_feedback, 1):
                print(f"{i}. {feedback.text}")
                print()
        else:
            print("No actionable feedback items found.")
        print("-" * 40)
        
        # Summary statistics
        print("\n📊 SUMMARY:")
        print(f"   Email length: {len(generated_email)} characters")
        print(f"   Feedback items: {len(review_result.actionable_feedback)}")
        print(f"   Should regenerate: {review_result.should_regenerate}")
        print(f"   Template used: {bool(template_info)}")
        
        # Assertions for test validation
        assert generated_email is not None
        assert len(generated_email) > 100  # Reasonable email length
        assert review_result is not None
        assert review_result.email_content == generated_email
        assert review_result.critique is not None
        assert len(review_result.critique) > 20  # Reasonable critique length
        
        print("\n✅ Integration test completed successfully!")
        print("="*60)
    
    def test_dj_outreach_with_mocked_llm(
        self,
        app_config,
        chat_history_manager,
        profile_manager,
        scroll_retriever
    ):
        """
        Test the DJ outreach flow with mocked LLM for faster testing.
        This version doesn't require OpenAI API key.
        """
        # Mock LLM responses
        mock_generated_email = """
        Subject: Professional DJ Services for Your Venue
        
        Dear Venue Manager,
        
        I hope this email finds you well. My name is Alex DJ, and I'm a professional DJ with 5 years of experience in the entertainment industry.
        
        I specialize in house music, hip-hop, and top 40 hits, and I've successfully performed at numerous weddings, corporate events, and clubs throughout the region. My dynamic mixing style and ability to read crowds have consistently resulted in memorable experiences for both clients and venues.
        
        I'm reaching out to explore potential booking opportunities at your venue. I believe my diverse musical repertoire and professional approach would be a great fit for your events.
        
        Would you be available for a brief conversation to discuss how we might collaborate? I'd love to learn more about your venue's needs and share how I can contribute to creating exceptional experiences for your guests.
        
        Thank you for considering my services. I look forward to hearing from you.
        
        Best regards,
        Alex DJ
        SoundWave Entertainment
        """
        
        mock_review_response = """
        ## CRITIQUE
        This email has a good professional structure and appropriate tone for venue outreach. The opening is courteous and the message clearly communicates the DJ's experience and specialization. However, it could benefit from more specific details about past successful events and a stronger call-to-action.
        
        ## FEEDBACK
         - Add specific examples of successful past events or venues
         - Include more compelling call-to-action with next steps
         - Consider adding availability or booking process details
         - Make the subject line more attention-grabbing
        
        ## RECOMMENDATION
        KEEP
        """
        
        # Set up the scenario
        user_prompt = "Write a DJ outreach email to venue managers"
        chat_history_manager.add_message(user_prompt, MessageType.INITIAL_PROMPT)
        
        # Create the LLMService and PromptBuilder instances
        llm_service = LLMService(app_config)
        prompt_builder = PromptBuilder(llm_service, chat_history_manager, profile_manager=profile_manager, scroll_retriever=scroll_retriever)
        review_agent = ReviewAgent(llm_service)
        
        # Patch generate_response on the LLMService instance
        with patch.object(llm_service, 'generate_response', return_value=mock_generated_email):
            # Generate the email
            prompt = prompt_builder.build_llm_prompt()
            generated_email = llm_service.generate_response(prompt, max_tokens=1500)
            assert generated_email is not None
            chat_history_manager.add_draft(generated_email)
        
        # Patch generate_response for review agent
        with patch.object(llm_service, 'generate_response', return_value=mock_review_response):
            review_result = review_agent.review_email(generated_email)
            assert review_result is not None
            assert len(review_result.actionable_feedback) == 5
            assert review_result.actionable_feedback[0].text.startswith("Add specific examples")
            assert review_result.critique.startswith("This email has a good professional structure")
            
            print("\n✅ Mocked integration test completed successfully!")
            print(f"📧 Generated email length: {len(generated_email)} characters")
            print(f"🔍 Review feedback items: {len(review_result.actionable_feedback)}") 