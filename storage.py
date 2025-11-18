import uuid
from typing import Dict, List, Any, Optional


class Storage:
    def __init__(self) -> None:
        self.resumes: List[Dict[str, Any]] = []
        self.analyses: List[Dict[str, Any]] = []
        self.interview_questions: List[Dict[str, Any]] = []
        self.roadmaps: List[Dict[str, Any]] = []
        self.user_progress: Dict[str, Dict[str, Any]] = {}

    def create_resume(self, data: Dict[str, Any]) -> Dict[str, Any]:
        resume = {
            "id": str(uuid.uuid4()),
            **data,
        }
        self.resumes.append(resume)
        if data["userId"] not in self.user_progress:
            self.user_progress[data["userId"]] = {
                "userId": data["userId"],
                "totalUploads": 0,
                "bestAtsScore": 0,
                "currentStreak": 0,
                "achievements": [],
                "lastUploadAt": None,
            }
        return resume

    def create_mock_analysis(self, resume_id: str, text: str) -> Dict[str, Any]:
        # Heuristic mock similar to TS version
        lower = text.lower()
        bullet_count = lower.count("\n-") + lower.count("\n•")
        has_sections = sum(1 for s in ["experience", "education", "skills", "projects"] if s in lower)
        found_skills = [s for s in ["react", "node", "javascript", "typescript", "python", "aws", "docker", "sql", "java", "go", "postgres", "mongodb", "kubernetes"] if s in lower]

        def clamp(n: float, min_v: float, max_v: float) -> float:
            return max(min_v, min(max_v, n))

        words = [w for w in lower.split() if w]
        word_count = len(words)
        keyword_coverage = clamp((len(found_skills) / max(6, 13)) * 100, 35, 95)
        format_signals = clamp((has_sections * 18) + (bullet_count * 2), 30, 92)
        grammar_signals = clamp(90 - (abs(650 - word_count) / 650) * 25, 55, 92)

        keyword_score = round(keyword_coverage)
        format_score = round(format_signals)
        grammar_score = round(grammar_signals)
        ats_score = round(0.35 * keyword_score + 0.3 * format_score + 0.35 * grammar_score)

        strengths: List[str] = []
        if len(found_skills) >= 5:
            strengths.append("Good coverage of in-demand technical skills")
        if bullet_count >= 6:
            strengths.append("Uses concise bullet points for readability")
        if has_sections >= 3:
            strengths.append("Well-structured with standard sections")
        if not strengths:
            strengths.append("Clear, readable formatting")

        improvements: List[str] = []
        if len(found_skills) < 4:
            improvements.append("Add more role-specific keywords to pass ATS")
        if word_count < 350:
            improvements.append("Expand experience with impact and scope")
        if word_count > 1000:
            improvements.append("Trim content to keep resume focused and scannable")
        if bullet_count < 4:
            improvements.append("Use bullet points to improve readability")

        issues: List[str] = []
        if has_sections < 3:
            issues.append("Missing common sections like Skills/Education/Projects")

        analysis = {
            "id": str(uuid.uuid4()),
            "resumeId": resume_id,
            "atsScore": ats_score,
            "grammarScore": grammar_score,
            "formatScore": format_score,
            "keywordScore": keyword_score,
            "feedback": {
                "strengths": strengths,
                "improvements": improvements,
                "issues": issues,
            },
            "skillsIdentified": found_skills if found_skills else ["communication", "problem solving"],
            "careerStage": "mid-level",
        }
        self.analyses.append(analysis)
        return analysis

    def create_mock_interview_questions(self, resume_id: str, text: str, count: int = 15) -> None:
        base = [
            {
                "id": str(uuid.uuid4()),
                "resumeId": resume_id,
                "question": "Tell me about a challenging project you worked on.",
                "sampleAnswer": "I faced X; I did Y; outcome was Z.",
                "type": "behavioral",
                "difficulty": "medium",
            },
            {
                "id": str(uuid.uuid4()),
                "resumeId": resume_id,
                "question": "Explain the difference between state and props in React.",
                "sampleAnswer": "State is internal; props come from parent.",
                "type": "technical",
                "difficulty": "easy",
            },
        ]
        self.interview_questions.extend(base[:count])

    def create_mock_roadmap(self, resume_id: str, skills_identified: List[str]) -> None:
        roadmap = {
            "id": str(uuid.uuid4()),
            "resumeId": resume_id,
            "currentSkills": [{"name": s, "level": "intermediate"} for s in skills_identified],
            "recommendedSkills": [
                {"name": "System Design", "priority": "high", "description": "Design scalable systems"},
                {"name": "Cloud Architecture", "priority": "high", "description": "Deepen AWS/GCP/Azure"},
            ],
            "actionPlan": [
                {"task": "Build project with auth", "estimatedWeeks": 4, "priority": 2},
                {"task": "Deploy app to cloud", "estimatedWeeks": 4, "priority": 2},
            ],
            "timelineWeeks": 8,
        }
        self.roadmaps.append(roadmap)

    def bump_progress(self, user_id: str, ats_score: int) -> None:
        p = self.user_progress.setdefault(user_id, {
            "userId": user_id,
            "totalUploads": 0,
            "bestAtsScore": 0,
            "currentStreak": 0,
            "achievements": [],
            "lastUploadAt": None,
        })
        p["totalUploads"] += 1
        p["bestAtsScore"] = max(p["bestAtsScore"], int(ats_score))
        p["currentStreak"] = p["totalUploads"]
        if p["bestAtsScore"] > 80 and "high_ats_score" not in p["achievements"]:
            p["achievements"].append("high_ats_score")

    def get_dashboard(self, user_id: str) -> Dict[str, Any]:
        user_progress = self.user_progress.get(user_id)
        latest_analysis = next((a for a in reversed(self.analyses) if any(r for r in self.resumes if r["id"] == a["resumeId"] and r["userId"] == user_id)), None)
        interview_questions: List[Dict[str, Any]] = []
        career_roadmap: Optional[Dict[str, Any]] = None

        if latest_analysis:
            user_resumes = [r for r in self.resumes if r["userId"] == user_id]
            latest_resume = user_resumes[-1] if user_resumes else None
            if latest_resume:
                interview_questions = [q for q in self.interview_questions if q["resumeId"] == latest_resume["id"]]
                career_roadmap = next((r for r in self.roadmaps if r["resumeId"] == latest_resume["id"]), None)

        return {
            "userProgress": user_progress,
            "latestAnalysis": latest_analysis,
            "interviewQuestions": interview_questions[:5],
            "careerRoadmap": career_roadmap,
            "totalInterviewQuestions": len(interview_questions),
        }

    def get_analysis_by_resume_id(self, resume_id: str) -> Optional[Dict[str, Any]]:
        return next((a for a in self.analyses if a["resumeId"] == resume_id), None)

    def get_interview_by_resume_id(self, resume_id: str) -> List[Dict[str, Any]]:
        return [q for q in self.interview_questions if q["resumeId"] == resume_id]

    def get_roadmap_by_resume_id(self, resume_id: str) -> Optional[Dict[str, Any]]:
        return next((r for r in self.roadmaps if r["resumeId"] == resume_id), None)

    def get_resumes_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        return [r for r in self.resumes if r["userId"] == user_id]


