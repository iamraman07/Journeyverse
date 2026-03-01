from app import app, db, Project, JourneyDay
from models import ProjectLike, ProjectComment
from datetime import datetime
import random

def add_sample_data():
    with app.app_context():
        # --- Define Global Seed Data ---
        users = ["JaneSmith", "SarahJ", "MikeT", "EmilyR", "ChrisP", "DavidW", "LisaM", "TomH"]
        comments_pool = [
            "This looks amazing! Can't wait on the updates.",
            "Great progress so far.",
            "I love the design direction.",
            "The backend logic seems solid.",
            "Have you considered adding dark mode?",
            "Scalability might be an issue with this approach.",
            "documentation is clear and helpful.",
            "Keep up the good work team!",
            "Interesting choice of tech stack.",
            "When is the beta release?"
        ]
        
        # --- Project 1: Alice (AI Personal Assistant) ---
        projects_data = [
            {
                "username": "Alice",
                "title": "AI Personal Assistant",
                "description": "AI-powered efficient Personal Assistant. This project aims to revolutionize how we manage our daily tasks by leveraging advanced large language models to provide proactive suggestions and automations. We focus on privacy and efficiency.",
                "members": ["Alice", "ramandeepkaur", "Bob", "Charlie", "Dave"],
                "days": [
                    {
                        "day": 1,
                        "entries": [
                            {"user": "Alice", "desc": "Kicked off the project with the team. Defined the core objectives and success metrics for the AI Personal Assistant."},
                            {"user": "ramandeepkaur", "desc": "Kickoff meeting! Outlined the core vision for the AI Assistant. We want something that feels proactive, not just reactive."},
                            {"user": "Bob", "desc": "Started setting up the backend infrastructure using Python and FastAPI. Defined the initial API endpoints for user authentication."},
                            {"user": "Charlie", "desc": "Researched various LLM APIs. Comparing GPT-4 vs Claude vs Llama 2 for our specific use case of task management."},
                            {"user": "Dave", "desc": "Created low-fidelity wireframes for the mobile app interface. Focusing on a clean, chat-centric UI."}
                        ]
                    },
                    {
                        "day": 2,
                        "entries": [
                            {"user": "Alice", "desc": "Reviewing the initial wireframes and technical specs. Gave feedback on the user onboarding flow."},
                            {"user": "ramandeepkaur", "desc": "Reviewed the wireframes with Dave. Suggested moving the voice command button to the center for better accessibility."},
                            {"user": "Bob", "desc": "Database schema design. Decided on PostgreSQL. Created tables for Users, Tasks, and Preferences."},
                            {"user": "Charlie", "desc": "Wrote a small prototype script to test context retention in conversations using LangChain."},
                            {"user": "Dave", "desc": "Refining UI based on feedback. Started working on the high-fidelity designs in Figma."}
                        ]
                    },
                    {
                        "day": 3,
                        "entries": [
                            {"user": "Alice", "desc": "Testing the initial authentication prototype. The flow feels smooth. Coordinating next steps for the MVP."},
                            {"user": "ramandeepkaur", "desc": "Planning the sprint for next week. We need to prioritize the notification system."},
                            {"user": "Bob", "desc": "Implemented JWT authentication. The login flow is now working securely."},
                            {"user": "Charlie", "desc": "Fine-tuning the system prompt to ensure the AI adopts a helpful and concise persona."},
                            {"user": "Dave", "desc": "Exported assets for the frontend team. Started looking into Flutter for cross-platform development."}
                        ]
                    }
                ]
            },
            {
                "username": "Raman",
                "title": "JourneyVerse - A futuristic social platform",
                "description": "JourneyVerse - A futuristic social platform. A space to track your daily progress and share your journey with the world. We are building a community of builders and learners.",
                "members": ["Raman", "John", "Sarah", "Mike"],
                "days": [
                    {
                        "day": 1,
                        "entries": [
                            {"user": "Raman", "desc": "Project Inception. Defined the core modules: Projects, Journeys, and Social Feed. The goal is transparency in building."},
                            {"user": "John", "desc": "Set up the Flask environment and configured the initial directory structure. Added a basic Hello World route."},
                            {"user": "Sarah", "desc": "Moodboarding for the UI. We want a deep blue 'Galaxy' theme to fit the 'Verse' branding."},
                            {"user": "Mike", "desc": "Researched database options. SQLAlchemy with SQLite for dev, moving to PostgreSQL for prod."}
                        ]
                    },
                    {
                        "day": 2,
                        "entries": [
                            {"user": "Raman", "desc": "Working on the Project Model. A project needs a creator, members, and a timeline."},
                            {"user": "John", "desc": "Implemented the User Registration and Login routes using Flask-Login and Bcrypt."},
                            {"user": "Sarah", "desc": "Designed the Project Card component. It needs to show progress and key stats at a glance."},
                            {"user": "Mike", "desc": "Created the initial migration script. The DB tables are now initialized."}
                        ]
                    },
                    {
                        "day": 3,
                        "entries": [
                            {"user": "Raman", "desc": "Integrated the frontend templates with the backend routes. The dashboard is starting to look real!"},
                            {"user": "John", "desc": "Added the 'Add Journey' functionality. Users can now post updates to their projects."},
                            {"user": "Sarah", "desc": "Polishing the CSS. Added some nice hover effects to the sidebar navigation."},
                            {"user": "Mike", "desc": "Wrote unit tests for the User model. Ensuring password hashing is robust."}
                        ]
                    }
                ]
            },
            {
                "username": "JohnDoe",
                "title": "E-commerce Website Redesign",
                "description": "E-commerce Website Redesign. Revamping the legacy platform to improve user experience and conversion rates. Introducing a modern tech stack and AI-driven recommendations.",
                "members": ["JohnDoe", "Alice", "Steve", "Natasha"],
                "days": [
                    {
                        "day": 1,
                        "entries": [
                            {"user": "JohnDoe", "desc": "Audit of the existing site. Identified key bottlenecks in the checkout process that cause drop-offs."},
                            {"user": "Alice", "desc": "Analyzing competitor sites. Dark mode and one-click checkout seem to be standard features now."},
                            {"user": "Steve", "desc": "Setting up the Next.js project. It offers great SEO and performance out of the box."},
                            {"user": "Natasha", "desc": " interviewing current users to understand their pain points. 'Too many steps' is the common complaint."}
                        ]
                    },
                    {
                        "day": 2,
                        "entries": [
                            {"user": "JohnDoe", "desc": "Drafting the new User Journey Map. Simplifying the flow from 'Product Page' to 'Order Confirmation'."},
                            {"user": "Alice", "desc": "Designing the new hero section. It needs to be visually striking and load instantly."},
                            {"user": "Steve", "desc": "Connecting to Stripe API. We need a secure and flexible payment gateway."},
                            {"user": "Natasha", "desc": "Compiling user interview data into a report for the stakeholders."}
                        ]
                    },
                    {
                        "day": 3,
                        "entries": [
                            {"user": "JohnDoe", "desc": "Reviewing the first draft of the homepage. The navigation is much cleaner now."},
                            {"user": "Alice", "desc": "Working on the mobile responsiveness. The menu needs to collapse gracefully."},
                            {"user": "Steve", "desc": "Implemented the shopping cart state management using Redux Toolkit."},
                            {"user": "Natasha", "desc": "Started writing the copy for the landing page. Focusing on benefits over features."}
                        ]
                    }
                ]
            }
        ]

        for p_data in projects_data:
            print(f"Processing project: {p_data['username']}...")
            
            # 1. Create/Get Project
            project = Project.query.filter_by(username=p_data['username']).first()
            if not project:
                project = Project(
                    username=p_data['username'],
                    date_and_time=datetime.now(),
                    project_description=f"{p_data['title']}\n{p_data['description']}", # Ensure title is in desc
                    members=",".join(p_data['members']),
                    likes=0,
                    comments=0
                )
                db.session.add(project)
                db.session.commit()
                print(f"  Created project record.")
            else:
                 # Update Description if needed to ensure Title is present
                 # and update members if old data
                 project.members = ",".join(p_data['members'])
                 if p_data['title'] not in project.project_description:
                     project.project_description = f"{p_data['title']}\n{p_data['description']}"
                 db.session.commit()
                 print(f"  Updated project record.")

            # 2. Clear old social/journey data to avoid dupes/mess
            JourneyDay.query.filter_by(project_id=project.id).delete()
            ProjectLike.query.filter_by(project_id=project.id).delete()
            ProjectComment.query.filter_by(project_id=project.id).delete()
            db.session.commit()

            # 3. Add Journey Days
            for day_data in p_data['days']:
                for entry in day_data['entries']:
                    jd = JourneyDay(
                        project_id=project.id,
                        day_number=day_data['day'],
                        member_name=entry['user'],  # Map user to member correctly
                        description=entry['desc']
                    )
                    db.session.add(jd)

            
            # 4. Add Likes
            num_likes = random.randint(3, 8)
            likers = random.sample(users, num_likes)
            for liker in likers:
                like = ProjectLike(project_id=project.id, user_name=liker)
                db.session.add(like)
            project.likes = num_likes

            # 5. Add Comments
            num_comments = random.randint(2, 6)
            commenters = random.sample(users, num_comments)
            for commenter in commenters:
                txt = random.choice(comments_pool)
                com = ProjectComment(project_id=project.id, user_name=commenter, comment_text=txt)
                db.session.add(com)
            project.comments = num_comments
            
            db.session.commit()
            print(f"  Populated {num_likes} likes, {num_comments} comments, and journey entries.")

        print("All sample data updated successfully.")

if __name__ == "__main__":
    add_sample_data()
