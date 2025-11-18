import os
import asyncio
import concurrent.futures
from typing import Any, Dict, List


class GeminiClient:
    def __init__(self) -> None:
        # Lazy import to avoid import error if dependency missing during tooling
        from google import genai  # type: ignore
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY or GOOGLE_API_KEY environment variable")
        self.client = genai.Client(api_key=api_key)
        self.fast_model = os.environ.get("GEMINI_FAST_MODEL", "gemini-2.0-flash")
        self.quality_model = os.environ.get("GEMINI_QUALITY_MODEL", "gemini-2.5-pro")

    def _generate_json(self, model: str, system_instruction: str, content: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        # The python SDK supports response_mime_type and response_schema
        response = self.client.models.generate_content(
            model=model,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": schema,
            },
            contents=content,
        )
        raw = getattr(response, "text", None)
        if not raw:
            raise RuntimeError("Empty response from Gemini")
        import json
        return json.loads(raw)

    def analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        system_prompt = (
            "You are an expert resume analyzer and ATS specialist. "
            "Analyze the provided resume text and provide comprehensive feedback.\n\n"
            "Provide scores (0-100) for:\n"
            "- ats_score: ATS (Applicant Tracking System) compatibility and keyword optimization\n"
            "- overall_score: Overall resume quality and effectiveness\n"
            "- keyword_match: Relevance and density of industry keywords\n"
            "- format_quality: Structure, organization, and visual appeal\n"
            "- grammar_style: Language quality, grammar, and writing style\n"
            "- content_strength: Impact of achievements, quantified results, and experience depth\n\n"
            "Identify:\n"
            "- strengths: Top 3-5 strong points (skills, achievements, experiences)\n"
            "- improvements: 3-5 areas for improvement (missing skills, weak experience, etc.)\n"
            "- issues: 2-4 critical problems (formatting issues, inconsistent dates, missing sections)\n"
            "- skills: 10-20 technical and professional skills identified\n"
            "- career stage: Current career level (entry, junior, mid, senior, executive)"
        )
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "ats_score": {"type": "number", "minimum": 0, "maximum": 100},
                "overall_score": {"type": "number", "minimum": 0, "maximum": 100},
                "keyword_match": {"type": "number", "minimum": 0, "maximum": 100},
                "format_quality": {"type": "number", "minimum": 0, "maximum": 100},
                "grammar_style": {"type": "number", "minimum": 0, "maximum": 100},
                "content_strength": {"type": "number", "minimum": 0, "maximum": 100},
                "feedback": {
                    "type": "object",
                    "properties": {
                        "strengths": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 5},
                        "improvements": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 5},
                        "issues": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 4},
                    },
                    "required": ["strengths", "improvements", "issues"],
                },
                "skillsIdentified": {"type": "array", "items": {"type": "string"}, "minItems": 10, "maxItems": 20},
                "careerStage": {"type": "string", "enum": ["entry", "junior", "mid", "senior", "executive"]},
            },
            "required": [
                "ats_score",
                "overall_score",
                "keyword_match", 
                "format_quality",
                "grammar_style",
                "content_strength",
                "feedback",
                "skillsIdentified",
                "careerStage",
            ],
        }
        result = self._generate_json(
            model=self.fast_model,
            system_instruction=system_prompt,
            content=f"Analyze this resume:\n\n{resume_text}",
            schema=schema,
        )
        return result

    def generate_technical_questions(self, resume_text: str, count: int = 10) -> List[Dict[str, Any]]:
        system_prompt = (
            f"You are an expert technical interviewer. Generate {count} technical interview questions based on the resume.\n"
            "Focus ONLY on technical questions related to:\n"
            "- Programming languages and frameworks mentioned\n"
            "- Technical skills and tools\n"
            "- System design and architecture\n"
            "- Problem-solving and coding challenges\n"
            "- Technology-specific best practices\n\n"
            "Each question should include: question, sampleAnswer (2-3 sentences), difficulty (easy/medium/hard)."
        )
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "sampleAnswer": {"type": "string"},
                            "type": {"type": "string", "enum": ["technical"]},
                            "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                        },
                        "required": ["question", "sampleAnswer", "type", "difficulty"],
                    },
                }
            },
            "required": ["questions"],
        }
        result = self._generate_json(
            model=self.fast_model,
            system_instruction=system_prompt,
            content=f"Generate technical interview questions for this resume:\n\n{resume_text}",
            schema=schema,
        )
        questions = result.get("questions", [])
        return questions[:count]

    def generate_career_roadmap(self, resume_text: str, skills_identified: List[str]) -> Dict[str, Any]:
        system_prompt = (
            "You are an expert career coach and industry advisor. Create a highly personalized career roadmap based on the resume content.\n\n"
            "Analyze the candidate's:\n"
            "- Current experience level and career trajectory\n"
            "- Technical skills and expertise areas\n"
            "- Industry and role focus\n"
            "- Career gaps and growth opportunities\n\n"
            "Provide:\n"
            "- currentSkills: Assess proficiency levels (beginner/intermediate/advanced/expert) for identified skills\n"
            "- recommendedSkills: Suggest 5-8 high-impact skills with priority (high/medium/low) and detailed descriptions\n"
            "- actionPlan: Create 6-10 specific, actionable tasks with realistic timelines (1-12 weeks) and priorities (1-5)\n"
            "- timelineWeeks: Overall roadmap duration (12-52 weeks)\n\n"
            "Focus on skills and actions that will have the biggest career impact for their specific role and industry."
        )
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "currentSkills": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "level": {"type": "string", "enum": ["beginner", "intermediate", "advanced", "expert"]},
                        },
                        "required": ["name", "level"],
                    },
                    "minItems": 5,
                    "maxItems": 15
                },
                "recommendedSkills": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                            "description": {"type": "string"},
                        },
                        "required": ["name", "priority", "description"],
                    },
                    "minItems": 5,
                    "maxItems": 8
                },
                "actionPlan": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string"},
                            "estimatedWeeks": {"type": "number", "minimum": 1, "maximum": 12},
                            "priority": {"type": "number", "minimum": 1, "maximum": 5},
                        },
                        "required": ["task", "estimatedWeeks", "priority"],
                    },
                    "minItems": 6,
                    "maxItems": 10
                },
                "timelineWeeks": {"type": "number", "minimum": 12, "maximum": 52},
            },
            "required": ["currentSkills", "recommendedSkills", "actionPlan", "timelineWeeks"],
        }
        result = self._generate_json(
            model=self.quality_model,
            system_instruction=system_prompt,
            content=(
                "Create a personalized career roadmap for this professional:\n\n" +
                f"Resume Content:\n{resume_text}\n\n" +
                f"Identified Skills: {', '.join(skills_identified)}\n\n" +
                "Focus on their specific industry, role, and career level to provide the most relevant recommendations."
            ),
            schema=schema,
        )
        return result

    def generate_all_content_parallel(self, resume_text: str) -> Dict[str, Any]:
        """Generate all content (analysis, questions, roadmap) in parallel for better performance"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all tasks
            analysis_future = executor.submit(self.analyze_resume, resume_text)
            questions_future = executor.submit(self.generate_technical_questions, resume_text, 10)
            
            # Wait for analysis to complete first (needed for roadmap)
            analysis = analysis_future.result()
            skills = analysis.get("skillsIdentified", [])
            
            # Submit roadmap task with skills
            roadmap_future = executor.submit(self.generate_career_roadmap, resume_text, skills)
            
            # Get remaining results
            questions = questions_future.result()
            roadmap = roadmap_future.result()
            
            return {
                "analysis": analysis,
                "technical_questions": questions,
                "roadmap": roadmap
            }


_client_singleton: GeminiClient | None = None


def get_client() -> GeminiClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = GeminiClient()
    return _client_singleton


