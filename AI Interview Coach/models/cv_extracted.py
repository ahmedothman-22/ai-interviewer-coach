
from typing import List, Optional
from pydantic import BaseModel, Field


class Experience(BaseModel):
    company: str = Field(description="The name of the company or organization where the candidate worked.")
    
    position: str = Field(
        description="The candidate's job title or position at the company."
    )
    start_date: Optional[str] = Field(
        description="The starting date of the employment. If the CV does not provide it, return 'Unknown'."
    )
    end_date: Optional[str] = Field(
        description="The ending date of the employment. If the candidate is still working there, return 'Present'. If unavailable, return 'Unknown'."
    )
    description: str = Field(
        description="A concise description of the candidate's responsibilities, achievements, and work performed in this position."
    )


class Education(BaseModel):
    institution: str = Field(
        description="The name of the university, college, school, or educational institution attended by the candidate."
    )
    degree: str = Field(
        description="The degree, diploma, or academic qualification obtained by the candidate."
    )
    field_of_study: str = Field(
        description="The candidate's major, specialization, or field of study."
    )
    start_date: Optional[str] = Field(
        description="The starting date of the education. If unavailable, return 'Unknown'."
    )
    end_date: Optional[str] = Field(
        description="The graduation or ending date of the education. If unavailable, return 'Unknown'."
    )

class Website(BaseModel):
    platform: str = Field(
        description="The name of the platform or website, such as GitHub, LinkedIn, Kaggle, GitLab, or Portfolio."
    )
    url: str = Field(
        description="The complete URL of the candidate's profile or website exactly as provided in the CV."
    )
    
    
class CVSchema(BaseModel):
    name: str = Field(
        description="The full name of the candidate exactly as it appears in the CV. If the name cannot be found, return 'Unknown'."
    )

    email: str = Field(
        description="The candidate's email address exactly as it appears in the CV. If no email address is provided, return 'Unknown'."
    )

    phone: str = Field(
        description="The candidate's phone number exactly as it appears in the CV. If no phone number is provided, return 'Unknown'."
    )

    location: str = Field(
        description="The candidate's city, country, or location as stated in the CV. If not provided, return 'Unknown'."
    )

    websites: List[Website] = Field(
    description="A list of professional online profiles and websites belonging to the candidate, including GitHub, LinkedIn, Kaggle, GitLab, portfolio, and personal websites.")
    
    summary: str = Field(
        description="A summary or professional profile of the candidate extracted from the CV. If no summary is provided, return 'Unknown'."
    )

    skills: List[str] = Field(
        description="A list of technical, professional, and interpersonal skills explicitly mentioned in the CV."
    )
    
  

    experience: List[Experience] = Field(
        description="A list of all professional work experiences mentioned in the CV, including company, position, dates, and responsibilities."
    )

    education: List[Education] = Field(
        description="A list of all educational qualifications mentioned in the CV, including institution, degree, field of study, and dates."
    )

    projects: List[str] = Field(
        description="A list of projects mentioned in the CV. Include the project name and a concise description of what the candidate built or accomplished."
    )

    certifications: List[str] = Field(
        description="A list of professional certifications, courses, or training programs explicitly mentioned in the CV."
    )

    languages: List[str] = Field(
        description="A list of languages the candidate can speak or use, including proficiency levels when they are provided in the CV."
    )



class AnswerEvaluation(BaseModel):

    score: float = Field(
        description="Overall technical score from 0 to 10."
    )

    technical_correctness: str = Field(
        description="Evaluation of whether the candidate's technical statements are correct."
    )

    relevance: str = Field(
        description="Evaluation of whether the candidate directly answered the interview question."
    )

    depth: str = Field(
        description="Evaluation of the depth of the candidate's understanding."
    )

    strengths: List[str] = Field(
        description="Specific strengths demonstrated in the candidate's answer."
    )

    missing_points: List[str] = Field(
        description="Important concepts or points that the candidate failed to mention."
    )

    mistakes: List[str] = Field(
        description="Specific technical mistakes or incorrect statements in the answer."
    )

    overall_feedback: str = Field(
        description="Concise overall feedback explaining the candidate's performance."
    )
