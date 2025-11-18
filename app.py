from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import time
import uuid
from services.parser import extract_text_from_file
from services.ai import get_client
from storage import Storage


def create_app():
    app = Flask(__name__)
    app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    storage = Storage()

    @app.route("/")
    def home():
        return render_template("home.html")
    
    @app.route("/upload")
    def upload_page():
        return render_template("upload.html")

    @app.route("/analysis")
    def analysis_page():
        return render_template("analysis.html")

    @app.route("/interview")
    def interview_page():
        return render_template("interview.html")

    @app.route("/roadmap")
    def roadmap_page():
        return render_template("roadmap.html")


    @app.post("/api/resumes/upload")
    def upload_resume():
        try:
            if "resume" not in request.files:
                return jsonify({"error": "No file uploaded"}), 400

            file = request.files["resume"]
            if file.filename == "":
                return jsonify({"error": "Empty filename"}), 400

            filename = secure_filename(file.filename)
            unique = f"{int(time.time()*1000)}-{os.getpid()}"
            ext = os.path.splitext(filename)[1]
            saved_name = f"{unique}{ext}"
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_name)
            file.save(file_path)

            try:
                extracted_text = extract_text_from_file(file_path)
            finally:
                # Cleanup uploaded file to mimic original behavior
                try:
                    os.remove(file_path)
                except Exception:
                    pass

            if not extracted_text or len(extracted_text.strip()) < 20:
                return jsonify({"error": "Could not extract text. The file may be empty, scanned, or unsupported."}), 422

            user_id = "default-user"
            resume = storage.create_resume({
                "userId": user_id,
                "filename": filename,
                "originalText": extracted_text,
            })

            # Use Gemini to analyze and generate outputs in parallel for better performance
            client = get_client()
            gemini_results = client.generate_all_content_parallel(extracted_text)
            analysis = gemini_results["analysis"]
            technical_questions = gemini_results["technical_questions"]
            roadmap = gemini_results["roadmap"]
            
            # Debug: Print what Gemini actually returned
            print("=== GEMINI ANALYSIS DEBUG ===")
            print(f"Analysis keys: {list(analysis.keys())}")
            print(f"ATS score: {analysis.get('ats_score', 'NOT FOUND')}")
            print(f"Overall score: {analysis.get('overall_score', 'NOT FOUND')}")
            print(f"Keyword match: {analysis.get('keyword_match', 'NOT FOUND')}")
            print(f"Format quality: {analysis.get('format_quality', 'NOT FOUND')}")
            print(f"Grammar style: {analysis.get('grammar_style', 'NOT FOUND')}")
            print(f"Content strength: {analysis.get('content_strength', 'NOT FOUND')}")
            print("=== END DEBUG ===")
            print(f"Technical questions count: {len(technical_questions)}")
            for i, q in enumerate(technical_questions[:2]):
                print(f"Q{i+1}: {q.get('question', 'NO QUESTION')[:50]}...")
            print("=== END QUESTIONS DEBUG ===")

            # Create analysis with new metrics
            analysis_row = {
                "id": str(uuid.uuid4()),
                "resumeId": resume["id"],
                "ats_score": int(analysis.get("ats_score", 75)),
                "overall_score": int(analysis.get("overall_score", 75)),
                "keyword_match": int(analysis.get("keyword_match", 70)),
                "format_quality": int(analysis.get("format_quality", 80)),
                "grammar_style": int(analysis.get("grammar_style", 85)),
                "content_strength": int(analysis.get("content_strength", 75)),
                "feedback": analysis.get("feedback", {"strengths": [], "improvements": [], "issues": []}),
                "skillsIdentified": analysis.get("skillsIdentified", []),
                "careerStage": analysis.get("careerStage", "mid"),
            }
            storage.analyses.append(analysis_row)

            # Add static behavioral questions + dynamic technical questions
            storage.interview_questions = [q for q in storage.interview_questions if q["resumeId"] != resume["id"]]
            
            # Add behavioral questions (static)
            behavioral_questions = [
                {
                    "id": "beh_1",
                    "resumeId": resume["id"],
                    "question": "Tell me about a time when you had to work under pressure to meet a tight deadline.",
                    "sampleAnswer": "I prioritized tasks, communicated with stakeholders, and delivered the project on time by working efficiently and staying focused.",
                    "type": "behavioral",
                    "difficulty": "medium",
                },
                {
                    "id": "beh_2", 
                    "resumeId": resume["id"],
                    "question": "Describe a situation where you had to resolve a conflict with a team member.",
                    "sampleAnswer": "I listened to their concerns, found common ground, and worked together to reach a solution that benefited the project.",
                    "type": "behavioral",
                    "difficulty": "medium",
                },
                {
                    "id": "beh_3",
                    "resumeId": resume["id"],
                    "question": "How do you handle feedback and criticism?",
                    "sampleAnswer": "I view feedback as an opportunity to grow, listen actively, and implement suggestions to improve my performance.",
                    "type": "behavioral", 
                    "difficulty": "easy",
                },
                {
                    "id": "beh_4",
                    "resumeId": resume["id"],
                    "question": "Tell me about a time you had to learn a new technology or skill quickly.",
                    "sampleAnswer": "I broke down the learning into manageable parts, used multiple resources, and applied the knowledge through hands-on practice.",
                    "type": "behavioral",
                    "difficulty": "medium",
                },
                {
                    "id": "beh_5",
                    "resumeId": resume["id"],
                    "question": "Describe a situation where you took initiative to improve a process or solve a problem.",
                    "sampleAnswer": "I identified inefficiencies, proposed solutions, and implemented changes that resulted in improved productivity and team satisfaction.",
                    "type": "behavioral",
                    "difficulty": "hard",
                }
            ]
            
            # Add situational questions (static)
            situational_questions = [
                {
                    "id": "sit_1",
                    "resumeId": resume["id"],
                    "question": "If you discovered a security vulnerability in production code, what would be your immediate steps?",
                    "sampleAnswer": "I would immediately assess the severity, document the vulnerability, notify the security team and management, implement a temporary fix if possible, and coordinate a proper patch deployment.",
                    "type": "situational",
                    "difficulty": "hard",
                },
                {
                    "id": "sit_2",
                    "resumeId": resume["id"],
                    "question": "How would you handle a situation where a project deadline is at risk due to technical challenges?",
                    "sampleAnswer": "I would analyze the blockers, communicate transparently with stakeholders about risks and options, propose solutions like scope reduction or timeline adjustment, and focus the team on critical path items.",
                    "type": "situational",
                    "difficulty": "medium",
                },
                {
                    "id": "sit_3",
                    "resumeId": resume["id"],
                    "question": "What would you do if you disagreed with a technical decision made by your team lead?",
                    "sampleAnswer": "I would prepare my concerns with data and alternatives, request a private discussion to present my viewpoint respectfully, listen to their reasoning, and support the final decision while documenting any risks.",
                    "type": "situational",
                    "difficulty": "medium",
                },
                {
                    "id": "sit_4",
                    "resumeId": resume["id"],
                    "question": "How would you approach debugging a performance issue in a system you're unfamiliar with?",
                    "sampleAnswer": "I would start by gathering metrics and logs, identify the bottleneck areas, review documentation and code, use profiling tools, and collaborate with team members familiar with the system.",
                    "type": "situational",
                    "difficulty": "hard",
                }
            ]
            
            # Add technical questions (dynamic from Gemini)
            for i, q in enumerate(technical_questions):
                storage.interview_questions.append({
                    "id": f"tech_{i}",
                    "resumeId": resume["id"],
                    "question": q.get("question"),
                    "sampleAnswer": q.get("sampleAnswer"),
                    "type": q.get("type"),
                    "difficulty": q.get("difficulty"),
                })
            
            # Add all question types
            storage.interview_questions.extend(behavioral_questions)
            storage.interview_questions.extend(situational_questions)
            
            # Store roadmap
            storage.roadmaps = [r for r in storage.roadmaps if r["resumeId"] != resume["id"]]
            storage.roadmaps.append({
                "id": resume["id"],
                "resumeId": resume["id"],
                **roadmap,
            })

            storage.bump_progress(user_id, int(analysis_row["overall_score"])) 

            return jsonify({
                "resume": resume,
                "analysis": analysis_row,
                "interviewQuestions": technical_questions + behavioral_questions + situational_questions,
                "careerRoadmap": roadmap,
                "processing": False,
                "message": "Resume uploaded. Analysis completed with Gemini.",
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.get("/api/dashboard")
    def dashboard():
        try:
            user_id = "default-user"
            data = storage.get_dashboard(user_id)
            if not data["userProgress"]:
                return jsonify({"error": "User progress not found"}), 404
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.get("/api/analysis/<resume_id>")
    def get_analysis(resume_id: str):
        try:
            analysis = storage.get_analysis_by_resume_id(resume_id)
            if not analysis:
                return jsonify({"error": "Analysis not found"}), 404
            return jsonify(analysis)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.get("/api/interview/<resume_id>")
    def get_interview(resume_id: str):
        try:
            questions = storage.get_interview_by_resume_id(resume_id)
            return jsonify(questions)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.get("/api/roadmap/<resume_id>")
    def get_roadmap(resume_id: str):
        try:
            roadmap = storage.get_roadmap_by_resume_id(resume_id)
            if not roadmap:
                return jsonify({"error": "Career roadmap not found"}), 404
            return jsonify(roadmap)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.get("/api/resumes")
    def get_resumes():
        try:
            user_id = "default-user"
            return jsonify(storage.get_resumes_by_user_id(user_id))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))


