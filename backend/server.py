from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np
from faker import Faker
import random


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

fake = Faker()

# Define Models
class Student(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    age: int
    gender: str
    enrollment_date: datetime
    status: str  # active, inactive, graduated

class Course(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    category: str
    difficulty: str  # beginner, intermediate, advanced
    duration_hours: int
    created_date: datetime

class Enrollment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    course_id: str
    enrollment_date: datetime
    completion_date: Optional[datetime] = None
    progress_percentage: float
    status: str  # enrolled, in_progress, completed, dropped

class Assessment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    course_id: str
    assessment_type: str  # quiz, assignment, exam, project
    score: float
    max_score: float
    completion_date: datetime

class LearningActivity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    course_id: str
    activity_type: str  # video_watch, reading, quiz_attempt, discussion
    duration_minutes: int
    date: datetime

class DashboardStats(BaseModel):
    total_students: int
    total_courses: int
    total_enrollments: int
    active_students: int
    completion_rate: float
    average_score: float

class StudentPerformance(BaseModel):
    student_id: str
    student_name: str
    courses_enrolled: int
    courses_completed: int
    average_score: float
    total_study_hours: float

class CourseAnalytics(BaseModel):
    course_id: str
    course_title: str
    total_enrollments: int
    completed_enrollments: int
    completion_rate: float
    average_score: float
    average_duration_hours: float

# Utility function to generate sample data
async def generate_sample_data():
    # Check if data already exists
    student_count = await db.students.count_documents({})
    if student_count > 0:
        return
    
    # Generate Students
    students = []
    for _ in range(150):
        student = Student(
            name=fake.name(),
            email=fake.email(),
            age=random.randint(18, 65),
            gender=random.choice(['Male', 'Female', 'Other']),
            enrollment_date=fake.date_time_between(start_date='-2y', end_date='now'),
            status=random.choices(['active', 'inactive', 'graduated'], weights=[70, 20, 10])[0]
        )
        students.append(student.dict())
    
    await db.students.insert_many(students)
    
    # Generate Courses
    course_categories = ['Programming', 'Data Science', 'Design', 'Business', 'Marketing', 'Mathematics']
    courses = []
    for _ in range(25):
        course = Course(
            title=fake.sentence(nb_words=4)[:-1],
            description=fake.paragraph(),
            category=random.choice(course_categories),
            difficulty=random.choice(['beginner', 'intermediate', 'advanced']),
            duration_hours=random.randint(10, 100),
            created_date=fake.date_time_between(start_date='-1y', end_date='now')
        )
        courses.append(course.dict())
    
    await db.courses.insert_many(courses)
    
    # Get created students and courses
    students_db = await db.students.find().to_list(length=None)
    courses_db = await db.courses.find().to_list(length=None)
    
    # Generate Enrollments
    enrollments = []
    for student in students_db:
        num_courses = random.randint(1, 8)
        selected_courses = random.sample(courses_db, min(num_courses, len(courses_db)))
        
        for course in selected_courses:
            enrollment_date = fake.date_time_between(
                start_date=max(student['enrollment_date'], course['created_date']),
                end_date='now'
            )
            
            progress = random.uniform(0, 100)
            status = 'completed' if progress >= 95 else ('in_progress' if progress > 0 else 'enrolled')
            completion_date = fake.date_time_between(enrollment_date, 'now') if status == 'completed' else None
            
            enrollment = Enrollment(
                student_id=student['id'],
                course_id=course['id'],
                enrollment_date=enrollment_date,
                completion_date=completion_date,
                progress_percentage=progress,
                status=status
            )
            enrollments.append(enrollment.dict())
    
    await db.enrollments.insert_many(enrollments)
    
    # Generate Assessments
    enrollments_db = await db.enrollments.find().to_list(length=None)
    assessments = []
    
    for enrollment in enrollments_db:
        if enrollment['progress_percentage'] > 20:  # Only create assessments for progressed enrollments
            num_assessments = random.randint(1, 5)
            for _ in range(num_assessments):
                max_score = random.choice([100, 50, 20, 10])
                score = random.uniform(0.4 * max_score, max_score)
                
                assessment = Assessment(
                    student_id=enrollment['student_id'],
                    course_id=enrollment['course_id'],
                    assessment_type=random.choice(['quiz', 'assignment', 'exam', 'project']),
                    score=score,
                    max_score=max_score,
                    completion_date=fake.date_time_between(
                        enrollment['enrollment_date'],
                        enrollment['completion_date'] or datetime.now()
                    )
                )
                assessments.append(assessment.dict())
    
    await db.assessments.insert_many(assessments)
    
    # Generate Learning Activities
    activities = []
    for enrollment in enrollments_db:
        if enrollment['progress_percentage'] > 0:
            num_activities = random.randint(5, 30)
            for _ in range(num_activities):
                activity = LearningActivity(
                    student_id=enrollment['student_id'],
                    course_id=enrollment['course_id'],
                    activity_type=random.choice(['video_watch', 'reading', 'quiz_attempt', 'discussion']),
                    duration_minutes=random.randint(5, 120),
                    date=fake.date_time_between(
                        enrollment['enrollment_date'],
                        enrollment['completion_date'] or datetime.now()
                    )
                )
                activities.append(activity.dict())
    
    await db.learning_activities.insert_many(activities)

# API Routes
@api_router.get("/")
async def root():
    return {"message": "LMS Analytics Dashboard API"}

@api_router.post("/initialize-data")
async def initialize_sample_data():
    """Initialize the database with sample LMS data"""
    try:
        await generate_sample_data()
        return {"message": "Sample data generated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/dashboard-stats")
async def get_dashboard_stats():
    """Get overall dashboard statistics"""
    try:
        total_students = await db.students.count_documents({})
        total_courses = await db.courses.count_documents({})
        total_enrollments = await db.enrollments.count_documents({})
        active_students = await db.students.count_documents({"status": "active"})
        
        # Calculate completion rate
        completed_enrollments = await db.enrollments.count_documents({"status": "completed"})
        completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
        
        # Calculate average score
        assessments = await db.assessments.find().to_list(length=None)
        if assessments:
            total_percentage = sum((a['score'] / a['max_score'] * 100) for a in assessments)
            average_score = total_percentage / len(assessments)
        else:
            average_score = 0
        
        return DashboardStats(
            total_students=total_students,
            total_courses=total_courses,
            total_enrollments=total_enrollments,
            active_students=active_students,
            completion_rate=round(completion_rate, 2),
            average_score=round(average_score, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/student-performance")
async def get_student_performance():
    """Get student performance analytics"""
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": "students",
                    "localField": "student_id", 
                    "foreignField": "id",
                    "as": "student"
                }
            },
            {"$unwind": "$student"},
            {
                "$group": {
                    "_id": "$student_id",
                    "student_name": {"$first": "$student.name"},
                    "courses_enrolled": {"$sum": 1},
                    "courses_completed": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    }
                }
            },
            {"$sort": {"courses_completed": -1}},
            {"$limit": 20}
        ]
        
        enrollment_data = await db.enrollments.aggregate(pipeline).to_list(length=None)
        
        # Get assessment data for each student
        performance_data = []
        for student_data in enrollment_data:
            assessments = await db.assessments.find({"student_id": student_data["_id"]}).to_list(length=None)
            activities = await db.learning_activities.find({"student_id": student_data["_id"]}).to_list(length=None)
            
            avg_score = 0
            if assessments:
                total_percentage = sum((a['score'] / a['max_score'] * 100) for a in assessments)
                avg_score = total_percentage / len(assessments)
            
            total_hours = sum(a['duration_minutes'] for a in activities) / 60
            
            performance_data.append(StudentPerformance(
                student_id=student_data["_id"],
                student_name=student_data["student_name"],
                courses_enrolled=student_data["courses_enrolled"],
                courses_completed=student_data["courses_completed"],
                average_score=round(avg_score, 2),
                total_study_hours=round(total_hours, 2)
            ))
        
        return performance_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/course-analytics")
async def get_course_analytics():
    """Get course analytics data"""
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": "courses",
                    "localField": "course_id",
                    "foreignField": "id",
                    "as": "course"
                }
            },
            {"$unwind": "$course"},
            {
                "$group": {
                    "_id": "$course_id",
                    "course_title": {"$first": "$course.title"},
                    "total_enrollments": {"$sum": 1},
                    "completed_enrollments": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    }
                }
            }
        ]
        
        enrollment_analytics = await db.enrollments.aggregate(pipeline).to_list(length=None)
        
        course_data = []
        for course_stats in enrollment_analytics:
            completion_rate = (course_stats["completed_enrollments"] / course_stats["total_enrollments"] * 100) if course_stats["total_enrollments"] > 0 else 0
            
            # Get assessment data for this course
            assessments = await db.assessments.find({"course_id": course_stats["_id"]}).to_list(length=None)
            avg_score = 0
            if assessments:
                total_percentage = sum((a['score'] / a['max_score'] * 100) for a in assessments)
                avg_score = total_percentage / len(assessments)
            
            # Get average study duration
            activities = await db.learning_activities.find({"course_id": course_stats["_id"]}).to_list(length=None)
            avg_duration = sum(a['duration_minutes'] for a in activities) / 60 / max(course_stats["total_enrollments"], 1)
            
            course_data.append(CourseAnalytics(
                course_id=course_stats["_id"],
                course_title=course_stats["course_title"],
                total_enrollments=course_stats["total_enrollments"],
                completed_enrollments=course_stats["completed_enrollments"],
                completion_rate=round(completion_rate, 2),
                average_score=round(avg_score, 2),
                average_duration_hours=round(avg_duration, 2)
            ))
        
        return course_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/enrollment-trends")
async def get_enrollment_trends():
    """Get enrollment trends over time"""
    try:
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$enrollment_date"},
                        "month": {"$month": "$enrollment_date"}
                    },
                    "enrollments": {"$sum": 1}
                }
            },
            {"$sort": {"_id.year": 1, "_id.month": 1}}
        ]
        
        trends = await db.enrollments.aggregate(pipeline).to_list(length=None)
        
        formatted_trends = []
        for trend in trends:
            formatted_trends.append({
                "month": f"{trend['_id']['year']}-{trend['_id']['month']:02d}",
                "enrollments": trend["enrollments"]
            })
        
        return formatted_trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/completion-by-category")
async def get_completion_by_category():
    """Get completion rates by course category"""
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": "courses",
                    "localField": "course_id",
                    "foreignField": "id",
                    "as": "course"
                }
            },
            {"$unwind": "$course"},
            {
                "$group": {
                    "_id": "$course.category",
                    "total_enrollments": {"$sum": 1},
                    "completed": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    }
                }
            }
        ]
        
        categories = await db.enrollments.aggregate(pipeline).to_list(length=None)
        
        category_data = []
        for cat in categories:
            completion_rate = (cat["completed"] / cat["total_enrollments"] * 100) if cat["total_enrollments"] > 0 else 0
            category_data.append({
                "category": cat["_id"],
                "total_enrollments": cat["total_enrollments"],
                "completed": cat["completed"],
                "completion_rate": round(completion_rate, 2)
            })
        
        return category_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()