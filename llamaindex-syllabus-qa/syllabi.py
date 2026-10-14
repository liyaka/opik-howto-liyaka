"""Writes three fictional course syllabi as PDFs into data/ (committed, regenerated if missing)."""

import pathlib

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate

DATA_DIR = pathlib.Path(__file__).parent / "data"

_base = getSampleStyleSheet()
TITLE = ParagraphStyle("T", parent=_base["Title"], fontSize=17, spaceAfter=4)
HEAD = ParagraphStyle("H", parent=_base["Heading2"], fontSize=12, spaceBefore=12, spaceAfter=3)
BODY = ParagraphStyle("B", parent=_base["Normal"], fontSize=10.5, leading=14, spaceAfter=5)

SYLLABI = {
    "cs340-databases.pdf": (
        "CS 340: Database Systems",
        "Larkspur University, Fall 2026. Instructor: Prof. Imani Okonkwo-Reyes.",
        [
            ("Prerequisites", "Students must have completed CS 220 (Data Structures) and "
             "MATH 201 (Discrete Mathematics) with a grade of C or better."),
            ("Grading", "Homework assignments count for 30% of the final grade, the midterm exam "
             "for 25%, the semester database project for 20%, and the final exam for 25%."),
            ("Late Work", "Homework and project submissions lose 10% of their score for each day "
             "they are late. Work more than five days late receives no credit."),
            ("Office Hours", "Prof. Okonkwo-Reyes holds office hours on Tuesdays and Thursdays "
             "from 2:00 to 4:00 pm in Calloway Hall, room 312."),
            ("Exam Dates", "The midterm exam is on Thursday, October 22, 2026, in class. The final "
             "exam is on Wednesday, December 16, 2026, from 9:00 am to 11:00 am."),
        ],
    ),
    "bio210-marine-ecology.pdf": (
        "BIO 210: Marine Ecology",
        "Larkspur University, Fall 2026. Instructor: Dr. Tobias Venn.",
        [
            ("Prerequisites", "BIO 101 (Introductory Biology) and CHEM 110 (General Chemistry). "
             "Students without CHEM 110 may enroll with the instructor's written permission."),
            ("Grading", "Lab reports make up 35% of the final grade, the field journal 15%, the "
             "midterm exam 20%, and the final exam 30%."),
            ("Late Work", "Lab reports lose 5% of their score per day late, for a maximum of three "
             "days. After three days a lab report is not accepted. The field journal cannot be "
             "submitted late."),
            ("Office Hours", "Dr. Venn is available on Wednesdays from 10:00 am to noon in "
             "Tidewater Hall, room 108, and by appointment."),
            ("Exam Dates", "The midterm exam is on Wednesday, October 21, 2026. The final exam is "
             "on Saturday, December 12, 2026, at 1:00 pm."),
        ],
    ),
    "hist115-maritime-trade.pdf": (
        "HIST 115: Maritime Trade and Empire",
        "Larkspur University, Fall 2026. Instructor: Prof. Saoirse Lindgren.",
        [
            ("Prerequisites", "There are no prerequisites. The course is open to all students."),
            ("Grading", "Two essays count for 20% each (40% total), weekly reading quizzes for 20%, "
             "class participation for 10%, and the final exam for 30%. There is no midterm."),
            ("Late Work", "Each student has one 48-hour grace token per semester, which extends any "
             "essay deadline with no penalty. Beyond that, essays lose one third of a letter grade "
             "per day late. Reading quizzes cannot be made up."),
            ("Office Hours", "Prof. Lindgren holds office hours on Mondays from 1:00 to 3:00 pm in "
             "Vance Library, room 2B."),
            ("Exam Dates", "The final exam is on Friday, December 18, 2026, from 2:00 pm to 4:00 pm. "
             "Essay 1 is due October 9 and Essay 2 is due November 20."),
        ],
    ),
}


def generate_all(directory: pathlib.Path = DATA_DIR) -> list[pathlib.Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for filename, (title, subtitle, sections) in SYLLABI.items():
        path = directory / filename
        story = [Paragraph(title, TITLE), Paragraph(subtitle, BODY)]
        for heading, text in sections:
            story += [Paragraph(heading, HEAD), Paragraph(text, BODY)]
        SimpleDocTemplate(
            str(path), pagesize=LETTER, title=title, author="Larkspur University",
            leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch,
            invariant=True,
        ).build(story)
        paths.append(path)
    return paths


if __name__ == "__main__":
    for p in generate_all():
        print("wrote", p)
