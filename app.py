import os
import re
import json
import requests
from flask import Flask, request, jsonify
from datetime import datetime, date

app = Flask(__name__)

# ================================================================
# ENVIRONMENT VARIABLES
# ================================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
META_TOKEN    = os.environ.get("META_TOKEN", "")
META_PHONE_ID = os.environ.get("META_PHONE_ID", "")
VERIFY_TOKEN  = os.environ.get("VERIFY_TOKEN", "vinay123")
# ================================================================
# TIMETABLE DATA
# ================================================================
TIMETABLE = {
    "monday": {
        "day": "Monday",
        "periods": [
            ("P1 10:00–11:00", "Major Practical (Lab)"),
            ("P2 11:00–12:00", "Major 1 Practical (Lab)"),
            ("P3 12:00–1:00",  "Major 1 Practical (Lab)"),
            ("LUNCH 1:00–2:15", "🍱 Lunch Break"),
            ("P4 2:15–3:15",   "Telugu / Sanskrit / Hindi (Room 126)"),
            ("P5 3:15–4:15",   "MDC (Room 102)"),
        ]
    },
    "tuesday": {
        "day": "Tuesday",
        "periods": [
            ("P1 10:00–11:00", "English (Room 207)"),
            ("P2 11:00–12:00", "AI Skill Course (Lab / Room 206)"),
            ("P3 12:00–1:00",  "Telugu / Sanskrit / Hindi (Room 203)"),
            ("LUNCH 1:00–2:15", "🍱 Lunch Break"),
            ("P4 2:15–3:15",   "Major 2 Practical (Lab / Room 206)"),
            ("P5 3:15–4:15",   "Major 2 Practical (Lab / Room 206)"),
        ]
    },
    "wednesday": {
        "day": "Wednesday",
        "periods": [
            ("P1 10:00–11:00", "Major 1 (Lab / Room 206)"),
            ("P2 11:00–12:00", "AI Skill Course (Lab / Room 206)"),
            ("P3 12:00–1:00",  "Major 2 (Lab / Room 206)"),
            ("LUNCH 1:00–2:15", "🍱 Lunch Break"),
            ("P4 2:15–3:15",   "Major (Lab / Room 206)"),
            ("P5 3:15–4:15",   "MDC (Room 206)"),
        ]
    },
    "thursday": {
        "day": "Thursday",
        "periods": [
            ("P1 10:00–11:00", "Major (Lab / Room 206)"),
            ("P2 11:00–12:00", "English (Room 202)"),
            ("P3 12:00–1:00",  "Major 1 (Lab / Room 206)"),
            ("LUNCH 1:00–2:15", "🍱 Lunch Break"),
            ("P4 2:15–3:15",   "Seminar (Lab / Room 206)"),
            ("P5 3:15–4:15",   "IKS (Room 206)"),
        ]
    },
    "friday": {
        "day": "Friday",
        "periods": [
            ("P1 10:00–11:00", "Major (Lab / Room 206)"),
            ("P2 11:00–12:00", "English (Room 206)"),
            ("P3 12:00–1:00",  "Telugu / Sanskrit / Hindi (Room 206)"),
            ("LUNCH 1:00–2:15", "🍱 Lunch Break"),
            ("P4 2:15–3:15",   "AI Skill Course (Lab / Room 206)"),
            ("P5 3:15–4:15",   "AI Subject (Room 101)"),
        ]
    },
    "saturday": {
        "day": "Saturday",
        "periods": [
            ("P1 10:00–11:00", "Telugu / Sanskrit / Hindi (Room 126)"),
            ("P2 11:00–12:00", "Major Practical (Lab)"),
            ("P3 12:00–1:00",  "Major Practical (Lab)"),
            ("LUNCH 1:00–2:15", "🍱 Lunch Break"),
            ("P4 2:15–3:15",   "Major (Lab / Room 206)"),
            ("P5 3:15–4:15",   "English (Room 206)"),
        ]
    },
}

DAY_NUMBER_MAP = {
    "1": "monday", "2": "tuesday", "3": "wednesday",
    "4": "thursday", "5": "friday", "6": "saturday",
}

DAY_ALIASES = {
    "mon": "monday", "monday": "monday", "somavaram": "monday",
    "tue": "tuesday", "tuesday": "tuesday", "mangalvaram": "tuesday",
    "wed": "wednesday", "wednesday": "wednesday", "budhavaram": "wednesday",
    "thu": "thursday", "thursday": "thursday", "guruvaram": "thursday",
    "fri": "friday", "friday": "friday", "shukravaram": "friday",
    "sat": "saturday", "saturday": "saturday", "shanivaram": "saturday",
}

# ================================================================
# FACULTY DATA
# ================================================================
FACULTY = [
    {
        "name": "Prof. K. Kameswara Rao",
        "role": "Professor & HoD (in-charge)",
        "qual": "MSc, MPhil, MTech, B.Ed.",
        "phone": "9670086068",
        "keywords": ["kameswara", "rao", "hod", "head"]
    },
    {
        "name": "Sri K.N.V.V.S.S. Chakravarthy",
        "role": "Contract Lecturer",
        "qual": "MS(IS), MPhil, MSc (Maths)",
        "phone": "9505123979",
        "keywords": ["chakravarthy", "chakra", "knvvss"]
    },
    {
        "name": "Sri V. Chennakesavulu Reddy",
        "role": "Contract Lecturer",
        "qual": "M.C.A., (M.Phil.)",
        "phone": "9494744008",
        "keywords": ["chennakesavulu", "reddy sir", "chennakesava"]
    },
    {
        "name": "Dr. P. Jyotsna",
        "role": "Contract Lecturer",
        "qual": "M.C.A., Ph.D.",
        "phone": "9704835308",
        "keywords": ["jyotsna", "jyothsna"]
    },
    {
        "name": "Smt. C. Kiranmayi",
        "role": "Contract Lecturer",
        "qual": "MSc, M.Phil.",
        "phone": "9866162367",
        "keywords": ["kiranmayi", "kiran mayi", "kiran"]
    },
    {
        "name": "Smt. N. Sudha Rani",
        "role": "Junior Computer Operator",
        "qual": "M.Sc., M.Phil.",
        "phone": "8106798250",
        "keywords": ["sudha", "sudha rani"]
    },
]

PRINCIPAL = {
    "name": "Prof. N. Venugopal Reddy",
    "qual": "MSc (Physics), M.Phil., Ph.D. & MSc (Maths)",
    "designation": "Principal",
    "phone": "+91 90004 89182"
}

# ================================================================
# STUDENT ROLL NUMBERS
# ================================================================
STUDENTS = {
    1:  "ANANTHA LAKSHMIKANTH",
    2:  "ANUMA VEERA KUMAR",
    3:  "B SANDEEP",
    4:  "BALA DINESH KARTHIK",
    5:  "BUSIRAJU VENKATA SAI",
    6:  "BUSSA GURUSUSANTH",
    7:  "E LAKSHMAN",
    8:  "GANGARAPU CHETHANA",
    9:  "GOPAL GARI SHANTHOSH",
    10: "GUNDLA LAKSHMIPATHI",
    11: "ITHEPALLI JAYA KUMAR",
    12: "KAMAKSHI SIVA REDDY",
    13: "KANCHAM RAJASEKHAR REDDY",
    14: "KAPALI HARI PRIYA",
    15: "KARIPAM ARAVIND",
    16: "KOMMALA PRASAD",
    17: "KURUBA CHANDU",
    18: "MALA DINESH KUMAR",
    19: "MALLARAPU VANI SREE",
    20: "MYLA TRINADH",
    21: "NESANURU VENKATESH",
    22: "PINJARI KHASIM",
    23: "P VINAY",
    24: "R ROHITH",
    25: "RAMOLLA BALAJI",
    26: "SINTA SAI CHARAN",
    27: "UPPU REDDY RANI",
    28: "V CHARAN",
    29: "VANAGANI BHARATH",
    30: "VANAGANI SREENATH",
}

def roll_str(num):
    return f"2502321{num:03d}"

# ================================================================
# SYLLABUS DATA
# ================================================================
SYLLABUS = {
    "1": {
        "title": "PYTHON PROGRAMMING AND DATA STRUCTURES",
        "units": [
            ("Unit 1 — Basics of Python", "Introduction, Features, Identifiers, Keywords, Data Types (Integer, Float, Boolean, String, Complex), Literals, Variables, Operators (Arithmetic, Relational, Logical, Bitwise, Assignment, Identity), Input/Output, Python Syntax (Lines, Comments, Indentation)."),
            ("Unit 2 — Control Flow and Functions", "if, if-else, if-elif-else. while, for, Nested Loops, break, continue, pass. Functions: Defining, Calling, Return, Scope (Local, Global), Arguments (Required, Positional, Default, *args **kwargs)."),
            ("Unit 3 — Sequence and Mapping Types", "Strings: Indexing, Slicing, Methods. Lists: Indexing, Slicing, Methods (append, count, extend, index, insert, pop). Tuples: Concatenation, Repetition, Membership. Dictionaries: keys, values, items, clear, copy, update."),
            ("Unit 4 — Object Oriented Programming", "Classes, Objects, Attributes, Methods. Constructor (__init__), Destructor (__del__). Encapsulation: Private (__), Public. Inheritance: Single, Multilevel, Multiple. Method Overriding, super()."),
            ("Unit 5 — Abstract Data Structures", "ADT: Concept and Importance. Linked List: Singly, Doubly — Node, Insertion, Deletion, Traversal. Stack: LIFO, push(), pop(). Queue: FIFO, enqueue(), dequeue()."),
        ]
    },
    "2": {
        "title": "ARTIFICIAL & COMPUTATIONAL INTELLIGENCE",
        "units": [
            ("Unit 1 — Introduction to AI & PEAS", "Definition, History, Applications, Scope of AI. PEAS: Performance, Environment, Actuators, Sensors. Intelligent Agents: Simple Reflex, Model-based, Goal-based, Utility-based. Rationality."),
            ("Unit 2 — Expert Systems", "Definition, Components: Knowledge Base, Inference Engine, User Interface. Rule-based systems, Knowledge Representation. Forward/Backward Chaining. Applications and Limitations."),
            ("Unit 3 — Search Strategies in AI", "Problem Formulation: State Space, Initial State, Goal Test. Uninformed: BFS, DFS, Uniform-cost. Informed: Greedy Best-First, A* Algorithm (f(n)=g(n)+h(n))."),
            ("Unit 4 — Machine Learning", "Definition, Types: Supervised, Unsupervised, Reinforcement. Classification, Regression, Clustering, Association Rules."),
            ("Unit 5 — Computational Intelligence & Ethics", "Fuzzy Logic, Neural Networks, Deep Learning basics. Ethics: Bias, Fairness, Transparency, Responsible AI."),
        ]
    },
    "3": {
        "title": "AI SKILL COURSE — APPLICATIONS OF AI",
        "units": [
            ("Unit 1 — Infrastructure & Platforms", "Hardware: CPU, GPU, TPU, NPU, RAM, Storage. Platforms: Google AutoML, Teachable Machine, Orange, KNIME, Weka, RapidMiner, H2O.ai. Edge AI vs Cloud AI."),
            ("Unit 2 — Foundations of Data", "Data vs Information vs Knowledge. Types: Structured, Semi-Structured, Unstructured. Modalities: Text, Image, Audio, Video, Tabular. Formats: CSV, JSON, XML, JPEG, MP3, MP4. Repositories: Kaggle, UCI, Hugging Face, Google Dataset."),
            ("Unit 3 — AI Data Pipeline", "Stages: Collection → Annotation → Cleaning → Splitting → Preprocessing → Training. Missing Values, Duplicates, Outliers, Noise. Normalization, Encoding."),
            ("Unit 4 — No-Code AI (Vibe Coding)", "Vibe Coding: Concept, Workflow, vs Traditional Coding. Tools: Firebase Studio, Replit, Cursor, Windsurf. Automation: Zapier, n8n, Power Automate, Lindy."),
            ("Unit 5 — AI in Networks, Cybersecurity & Forensics", "Networking: Traffic Prediction, IDS, Optimization. Cybersecurity: Threat Detection, Malware Analysis, Fraud. Digital Forensics: Evidence Analysis, Timeline Reconstruction."),
        ]
    },
}

# ================================================================
# IMPORTANT QUESTIONS
# ================================================================
IMP_QUESTIONS = {
    "1": {
        "title": "Python Programming & Data Structures",
        "top5": "⭐ Features of Python | OOP & Inheritance | Stack & Queue | Linked List | All Operators",
        "units": [
            ("Unit 1 — Basics of Python", (
                "*5 Mark Questions:*\n"
                "⭐ Features of Python\n"
                "⭐ Identifiers & Keywords with examples\n"
                "⭐ Python built-in data types with examples\n"
                "⭐ Python literals — types with examples\n"
                "⭐ Variables and assignment statements\n"
                "• Python syntax rules — indentation, comments\n"
                "• input() and print() with examples\n"
                "• Arithmetic & relational operators\n"
                "• Logical operators with truth table\n"
                "• Identity & bitwise operators\n"
                "• int, float, complex differences\n"
                "• Structure of a Python program\n\n"
                "*10 Mark Questions:*\n"
                "⭐ Python data types in detail\n"
                "⭐ Classification of operators with examples\n"
                "⭐ Input/output with all formatting options\n"
                "• Python syntax & program structure\n"
                "• Program demonstrating all operators\n"
                "• History, features & applications of Python"
            )),
            ("Unit 2 — Control Flow & Functions", (
                "*5 Mark Questions:*\n"
                "⭐ if statement with syntax & example\n"
                "⭐ if-else statement with example\n"
                "⭐ if-elif-else with example\n"
                "⭐ while loop with syntax & example\n"
                "⭐ for loop with syntax & example\n"
                "• Nested loops with example\n"
                "• break, continue and pass\n"
                "• Functions — definition, why needed\n"
                "• Local & global variables\n"
                "• Default & required arguments\n"
                "• *args and **kwargs\n"
                "• Recursion — factorial program\n\n"
                "*10 Mark Questions:*\n"
                "⭐ All conditional statements with examples\n"
                "⭐ for and while loops with examples\n"
                "⭐ Functions — definition, calling, return\n"
                "• All types of function arguments\n"
                "• Factorial using functions program\n"
                "• break, continue, pass differences"
            )),
            ("Unit 3 — Sequence & Mapping Types", (
                "*5 Mark Questions:*\n"
                "⭐ Strings — indexing and slicing\n"
                "⭐ String indexing — positive & negative\n"
                "⭐ String slicing with examples\n"
                "⭐ String operators — concatenation, repetition\n"
                "⭐ Lists — creation and indexing\n"
                "• List slicing and list comprehension\n"
                "• List methods: append, insert, pop, extend\n"
                "• Tuples — difference from lists\n"
                "• Tuple operations\n"
                "• Dictionaries — creation and access\n"
                "• Dictionary methods: keys, values, items\n"
                "• Mutable vs immutable types\n\n"
                "*10 Mark Questions:*\n"
                "⭐ Strings — indexing, slicing, all methods\n"
                "⭐ Lists — creation, slicing, all methods\n"
                "⭐ Tuples — creation, operations, vs list\n"
                "• Dictionaries — all methods with examples\n"
                "• Compare lists, tuples, dictionaries\n"
                "• All sequence types with examples"
            )),
            ("Unit 4 — Object Oriented Programming", (
                "*5 Mark Questions:*\n"
                "⭐ OOP — definition & principles\n"
                "⭐ Class and object — syntax for both\n"
                "⭐ Attributes and methods with example\n"
                "⭐ Constructor __init__() with example\n"
                "⭐ Destructor __del__ method\n"
                "• Encapsulation with example\n"
                "• Private & public members\n"
                "• Inheritance — why useful?\n"
                "• Single inheritance with example\n"
                "• Multilevel inheritance with example\n"
                "• Multiple inheritance with example\n"
                "• Method overriding & super()\n\n"
                "*10 Mark Questions:*\n"
                "⭐ OOP concepts — class, object, inheritance, encapsulation\n"
                "⭐ Classes & objects with complete programs\n"
                "⭐ Encapsulation — private/public members\n"
                "• All types of inheritance with examples\n"
                "• Program demonstrating all OOP features\n"
                "• Constructor & destructor with examples"
            )),
            ("Unit 5 — Abstract Data Structures", (
                "*5 Mark Questions:*\n"
                "⭐ ADT — definition & importance\n"
                "⭐ Linked list with diagram & advantages\n"
                "⭐ Node structure in singly linked list\n"
                "⭐ Insertion in singly linked list\n"
                "⭐ Deletion in singly linked list\n"
                "• Doubly linked list vs singly\n"
                "• Stack — LIFO with real-life example\n"
                "• push() and pop() with diagram\n"
                "• Queue — FIFO with real-life example\n"
                "• enqueue() and dequeue() with diagram\n"
                "• Applications of stack and queue\n"
                "• Compare stack and queue\n\n"
                "*10 Mark Questions:*\n"
                "⭐ ADT — concept, definition, importance\n"
                "⭐ Singly linked list — insert, delete, traverse\n"
                "⭐ Stack — LIFO, implementation in Python\n"
                "• Queue — FIFO, implementation in Python\n"
                "• Compare stack & queue with diagrams\n"
                "• Doubly linked list with operations"
            )),
        ]
    },
    "2": {
        "title": "Artificial & Computational Intelligence",
        "top5": "⭐ PEAS Framework | Expert Systems | BFS/DFS/A* | Types of ML | AI Ethics",
        "units": [
            ("Unit 1 — Introduction to AI & Agents", (
                "*5 Mark Questions:*\n"
                "⭐ Define AI — history and scope\n"
                "⭐ Applications of AI in real life\n"
                "⭐ PEAS framework — all components\n"
                "⭐ Intelligent Agent — definition & properties\n"
                "⭐ Simple Reflex Agent with diagram\n"
                "• Model-based Reflex Agent with diagram\n"
                "• Goal-based Agent with diagram\n"
                "• Utility-based Agent with diagram\n"
                "• Rationality & rational agents\n"
                "• AI vs ML vs Deep Learning\n"
                "• Agent architecture\n"
                "• AI in healthcare and education\n\n"
                "*10 Mark Questions:*\n"
                "⭐ History, definition & scope of AI\n"
                "⭐ PEAS framework with real-world examples\n"
                "⭐ All four types of intelligent agents\n"
                "• Rationality & rational agents\n"
                "• AI applications in various domains\n"
                "• Intelligent agent architecture with diagram"
            )),
            ("Unit 2 — Expert Systems", (
                "*5 Mark Questions:*\n"
                "⭐ Expert System — definition & characteristics\n"
                "⭐ Architecture of Expert System with diagram\n"
                "⭐ Knowledge Base — role in Expert Systems\n"
                "⭐ Inference Engine — forward & backward chaining\n"
                "⭐ User Interface component\n"
                "• Knowledge representation — rule-based\n"
                "• Semantic networks\n"
                "• Applications of Expert Systems\n"
                "• Advantages & disadvantages of ES\n"
                "• ES vs traditional computer programs\n"
                "• Frames in knowledge representation\n"
                "• Forward chaining with example\n\n"
                "*10 Mark Questions:*\n"
                "⭐ Complete architecture of Expert Systems\n"
                "⭐ Knowledge representation techniques\n"
                "⭐ Applications, advantages & limitations of ES\n"
                "• Forward and backward chaining\n"
                "• Expert System — components, working\n"
                "• ES vs human experts"
            )),
            ("Unit 3 — Search Strategies in AI", (
                "*5 Mark Questions:*\n"
                "⭐ Problem formulation — state space\n"
                "⭐ Initial state, goal state, goal test\n"
                "⭐ BFS algorithm with steps\n"
                "⭐ DFS algorithm with steps\n"
                "⭐ Compare BFS and DFS\n"
                "• Uniform Cost Search\n"
                "• Greedy Best-First Search\n"
                "• A* algorithm — f(n)=g(n)+h(n)\n"
                "• Heuristic function with examples\n"
                "• Informed vs uninformed search\n"
                "• Time & space complexity of BFS\n"
                "• Search tree with example\n\n"
                "*10 Mark Questions:*\n"
                "⭐ BFS — steps, example, complexity, diagram\n"
                "⭐ DFS — steps, example, comparison with BFS\n"
                "⭐ A* algorithm — f(n)=g(n)+h(n), working\n"
                "• Compare all search strategies\n"
                "• Problem formulation with example\n"
                "• Informed vs uninformed search"
            )),
            ("Unit 4 — Introduction to Machine Learning", (
                "*5 Mark Questions:*\n"
                "⭐ Define Machine Learning — why needed?\n"
                "⭐ Supervised Learning with examples\n"
                "⭐ Unsupervised Learning with examples\n"
                "⭐ Reinforcement Learning with example\n"
                "⭐ Classification in ML with example\n"
                "• Regression with example\n"
                "• Clustering with example\n"
                "• Association Rules in ML\n"
                "• Training data & testing data\n"
                "• Overfitting — how to prevent\n"
                "• Linear Regression briefly\n"
                "• KNN algorithm briefly\n\n"
                "*10 Mark Questions:*\n"
                "⭐ Types of ML — Supervised, Unsupervised, Reinforcement\n"
                "⭐ Supervised vs Unsupervised — comparison\n"
                "⭐ Classification vs Regression vs Clustering\n"
                "• Training/testing, overfitting, underfitting\n"
                "• ML algorithms — Linear Regression, KNN\n"
                "• ML — types and real-world applications"
            )),
            ("Unit 5 — Computational Intelligence & Ethics", (
                "*5 Mark Questions:*\n"
                "⭐ Computational Intelligence — techniques\n"
                "⭐ Fuzzy Logic vs crisp logic\n"
                "⭐ Membership functions in Fuzzy Logic\n"
                "⭐ Applications of Fuzzy Logic\n"
                "⭐ Biological Neuron — structure\n"
                "• Artificial Neuron — working\n"
                "• Perceptron with diagram\n"
                "• Deep Learning basics\n"
                "• Ethics in AI — why important?\n"
                "• Bias and Fairness in AI\n"
                "• Transparency in AI\n"
                "• Responsible AI principles\n\n"
                "*10 Mark Questions:*\n"
                "⭐ Fuzzy Logic — crisp vs fuzzy, membership functions\n"
                "⭐ Neural Networks — biological neuron, perceptron\n"
                "⭐ Ethics in AI — bias, fairness, transparency\n"
                "• Computational Intelligence techniques\n"
                "• Crisp Logic vs Fuzzy Logic comparison\n"
                "• Ethical challenges & responsible AI"
            )),
        ]
    },
    "3": {
        "title": "AI Skill Course — Applications of AI",
        "top5": "⭐ CPU/GPU/TPU/NPU | Edge AI | Data Pipeline | Vibe Coding | AI Cybersecurity",
        "units": [
            ("Unit 1 — AI Infrastructure & Platforms", (
                "*5 Mark Questions:*\n"
                "⭐ CPU — role in AI computations\n"
                "⭐ GPU — why preferred for AI/Deep Learning\n"
                "⭐ TPU (Tensor Processing Unit) — advantages\n"
                "⭐ NPU (Neural Processing Unit) — where used\n"
                "⭐ Compare CPU, GPU, TPU and NPU\n"
                "• Edge AI — concept and working\n"
                "• Real-world applications of Edge AI\n"
                "• Cloud AI vs Edge AI\n"
                "• Google AutoML platform\n"
                "• Teachable Machine by Google\n"
                "• Orange and KNIME platforms\n"
                "• AI platforms — list any three\n\n"
                "*10 Mark Questions:*\n"
                "⭐ CPU vs GPU vs TPU vs NPU — table comparison\n"
                "⭐ Edge AI — definition, working, applications\n"
                "⭐ AI platforms — AutoML, Teachable Machine, Orange\n"
                "• Cloud AI vs Edge AI — pros/cons\n"
                "• Hardware requirements for AI\n"
                "• Role of GPU in AI/ML"
            )),
            ("Unit 2 — Foundations of Data", (
                "*5 Mark Questions:*\n"
                "⭐ Data vs Information vs Knowledge\n"
                "⭐ Structured Data with examples\n"
                "⭐ Unstructured Data with examples\n"
                "⭐ Semi-Structured Data — CSV and JSON\n"
                "⭐ Data modalities — text, image, audio, video\n"
                "• Data formats — CSV, JSON, XML\n"
                "• Kaggle — importance as dataset repository\n"
                "• UCI Machine Learning Repository\n"
                "• Hugging Face — role in AI\n"
                "• Structured vs unstructured comparison\n"
                "• Metadata — why important in AI\n"
                "• Data quality importance in AI/ML\n\n"
                "*10 Mark Questions:*\n"
                "⭐ Data vs Information vs Knowledge — differences\n"
                "⭐ Structured, Semi-Structured, Unstructured comparison\n"
                "⭐ Data modalities — formats and examples\n"
                "• Dataset repositories — Kaggle, UCI, Hugging Face\n"
                "• Data formats — CSV, JSON, XML, JPEG, MP3\n"
                "• Importance of data in AI — quality & sources"
            )),
            ("Unit 3 — AI Data Pipeline", (
                "*5 Mark Questions:*\n"
                "⭐ AI Data Pipeline — all stages\n"
                "⭐ Data Collection stage\n"
                "⭐ Data Annotation — types\n"
                "⭐ Data Labeling — importance\n"
                "⭐ Data Cleaning — missing values\n"
                "• Outliers — detection & removal\n"
                "• Data Splitting — train/test/validation\n"
                "• Data Preprocessing — normalization\n"
                "• Feature selection — why needed\n"
                "• Data encoding — one-hot encoding\n"
                "• Importance of each pipeline stage\n"
                "• Noise in data — how removed\n\n"
                "*10 Mark Questions:*\n"
                "⭐ All stages of AI Data Pipeline in detail\n"
                "⭐ Data Cleaning — missing values, outliers, noise\n"
                "⭐ Data Annotation & Labeling — types, tools\n"
                "• Data Preprocessing — normalization, encoding\n"
                "• Data Splitting — ratios and importance\n"
                "• Complete AI Data Pipeline with diagram"
            )),
            ("Unit 4 — No-Code AI (Vibe Coding)", (
                "*5 Mark Questions:*\n"
                "⭐ Vibe Coding — concept\n"
                "⭐ Workflow of Vibe Coding\n"
                "⭐ Vibe Coding vs Traditional Coding\n"
                "⭐ Benefits of Vibe Coding\n"
                "⭐ Firebase Studio as no-code AI tool\n"
                "• Replit as AI development platform\n"
                "• Cursor for Vibe Coding\n"
                "• Workflow automation — importance\n"
                "• Zapier — features and use cases\n"
                "• n8n vs Zapier differences\n"
                "• Microsoft Power Automate\n"
                "• AI workflows without coding examples\n\n"
                "*10 Mark Questions:*\n"
                "⭐ Vibe Coding — concept, workflow, benefits\n"
                "⭐ Vibe Coding vs Traditional Programming\n"
                "⭐ Automation tools — Zapier, n8n, Power Automate\n"
                "• No-code tools — Firebase, Replit, Cursor\n"
                "• AI workflows without programming\n"
                "• Workflow automation — definition & tools"
            )),
            ("Unit 5 — AI in Networks, Cybersecurity & Forensics", (
                "*5 Mark Questions:*\n"
                "⭐ AI in Networking\n"
                "⭐ Traffic prediction using AI\n"
                "⭐ IDS (Intrusion Detection System)\n"
                "⭐ Network optimization using AI\n"
                "⭐ Cybersecurity — how AI improves it\n"
                "• Threat detection using AI\n"
                "• Malware analysis — how AI detects\n"
                "• Fraud detection with example\n"
                "• Challenges of AI in cybersecurity\n"
                "• Digital Forensics — AI assistance\n"
                "• Evidence analysis using AI\n"
                "• Timeline reconstruction in forensics\n\n"
                "*10 Mark Questions:*\n"
                "⭐ AI in Networking — traffic, IDS, optimization\n"
                "⭐ AI in Cybersecurity — threat, malware, fraud\n"
                "⭐ AI in Digital Forensics — evidence, timeline\n"
                "• Compare AI in Networking, Cybersecurity, Forensics\n"
                "• Challenges & future scope of AI in cybersecurity\n"
                "• AI transforming Networks, Cybersecurity & Forensics"
            )),
        ]
    },
}

# ================================================================
# EXAM SCHEDULE
# ================================================================
EXAM_SCHEDULE = """📅 *Exam Schedule — BSc AI 2025-26*
━━━━━━━━━━━━━━━━━━━━━━
📚 Classes Started    : 21 Feb 2026
📝 Mid-Term Exam I    : 25 Mar – 31 Mar 2026
📝 Mid-Term Exam II   : 24 Apr – 30 Apr 2026
🏫 Last Day of Class  : 5 May 2026
📖 Semester Theory    : 8 May – 15 May 2026
🔬 Semester Practical : 16 May – 19 May 2026
☀️ Summer Vacation    : 16 May – 20 Jun 2026
🎓 Semester III Begins: 29 Jun 2026
━━━━━━━━━━━━━━━━━━━━━━
All the best! 🙏"""

# ================================================================
# PYTHON CODE SNIPPETS
# ================================================================
CODE_SNIPPETS = {
    "print": '```\nprint("Hello, World!")\nname = input("Your name: ")\nprint("Hello,", name)\n```',
    "input": '```\nname = input("Enter name: ")\nage = int(input("Enter age: "))\nprint(f"Name: {name}, Age: {age}")\n```',
    "if": '```\nx = int(input("Enter number: "))\nif x > 0:\n    print("Positive")\nelif x < 0:\n    print("Negative")\nelse:\n    print("Zero")\n```',
    "for": '```\n# For loop example\nfor i in range(1, 6):\n    print(i)\n\n# Loop through list\nfruits = ["apple", "mango", "banana"]\nfor fruit in fruits:\n    print(fruit)\n```',
    "while": '```\n# While loop\ni = 1\nwhile i <= 5:\n    print(i)\n    i += 1\n```',
    "function": '```\ndef greet(name, msg="Hello"):\n    return f"{msg}, {name}!"\n\nprint(greet("Vinay"))\nprint(greet("Chandu", "Namaste"))\n```',
    "list": '```\nmy_list = [10, 20, 30, 40]\nmy_list.append(50)    # add end\nmy_list.insert(0, 5)  # add start\nmy_list.pop()         # remove last\nprint(my_list)\nprint(my_list[1:3])   # slicing\n```',
    "dict": '```\nstudent = {"name": "Vinay", "roll": 23, "marks": 95}\nprint(student["name"])\nstudent["marks"] = 98\nfor key, val in student.items():\n    print(key, ":", val)\n```',
    "class": '```\nclass Student:\n    def __init__(self, name, roll):\n        self.name = name\n        self.roll = roll\n    def display(self):\n        print(f"Name: {self.name}, Roll: {self.roll}")\n\ns = Student("Vinay", 23)\ns.display()\n```',
    "stack": '```\n# Stack using list (LIFO)\nstack = []\nstack.append(10)  # push\nstack.append(20)\nstack.append(30)\nprint("Top:", stack[-1])\nstack.pop()       # pop\nprint("Stack:", stack)\n```',
    "queue": '```\n# Queue using list (FIFO)\nqueue = []\nqueue.append("A")  # enqueue\nqueue.append("B")\nqueue.append("C")\nprint("Front:", queue[0])\nqueue.pop(0)       # dequeue\nprint("Queue:", queue)\n```',
}

# ================================================================
# JOKES
# ================================================================
JOKES = [
    "Why do programmers prefer dark mode? 😄\nBecause light attracts bugs! 🐛",
    "Why did the Python programmer fail the exam? 😂\nBecause they kept saying: *IndentationError* 😆",
    "A loop walks into a bar...\nA loop walks into a bar...\nA loop walks into a bar... 🔁",
    "What do you call a sleeping computer? 💤\n*Hardware!* 😂",
    "Why don't scientists trust atoms? 🤔\nBecause they make up everything! 😂",
]
joke_index = [0]

# ================================================================
# MOTIVATION MESSAGES
# ================================================================
MOTIVATIONS = [
    "🌟 *You've got this, BSc AI student!*\n\nEvery expert was once a beginner.\nStart with just one page today.\nProgress > Perfection! 💪\n\n*Om Namo Venkatesaya!* 🙏",
    "📚 *Padalekapotunna?*\n\nThat feeling means you're trying! 🔥\nBreak it down: 1 unit = 20 minutes.\nYou CAN do this!\n\n*All the best!* 🙏",
    "⭐ *Exam stress?*\n\nRemember: Difficulty is temporary.\nYour degree is permanent! 🎓\nStudy smart, not just hard! 💡\n\n*S.V. Arts College believes in you!* 🙏",
    "🚀 *Don't give up!*\n\nAI students are building the future.\nThat future needs YOU in it!\nOne step at a time. 🌈\n\n*Jai Venkatesha!* 🙏",
]
motivation_index = [0]

# ================================================================
# QUIZ QUESTIONS
# ================================================================
QUIZ_QUESTIONS = [
    {
        "q": "What does PEAS stand for in AI?",
        "options": ["A) Process, Execution, Action, Storage\nB) Performance, Environment, Actuators, Sensors\nC) Programming, Estimation, Algorithm, System\nD) Planning, Execution, Analysis, Search"],
        "answer": "B",
        "explain": "PEAS = Performance measure, Environment, Actuators, Sensors — used to describe intelligent agents!"
    },
    {
        "q": "Which data structure follows LIFO principle?",
        "options": ["A) Queue\nB) Linked List\nC) Stack\nD) Array"],
        "answer": "C",
        "explain": "Stack = Last In First Out (LIFO). Like a stack of plates! 🍽️"
    },
    {
        "q": "What is the time complexity of BFS?",
        "options": ["A) O(log n)\nB) O(n²)\nC) O(V+E)\nD) O(n)"],
        "answer": "C",
        "explain": "BFS time complexity = O(V+E) where V=Vertices, E=Edges in the graph."
    },
    {
        "q": "Which Python keyword is used to define a function?",
        "options": ["A) function\nB) define\nC) def\nD) func"],
        "answer": "C",
        "explain": "In Python, 'def' keyword defines a function. Example: def my_function():"
    },
    {
        "q": "Which type of ML has no labeled training data?",
        "options": ["A) Supervised Learning\nB) Reinforcement Learning\nC) Deep Learning\nD) Unsupervised Learning"],
        "answer": "D",
        "explain": "Unsupervised Learning = no labels! It finds patterns on its own. (e.g., Clustering)"
    },
    {
        "q": "What does A* algorithm use that BFS doesn't?",
        "options": ["A) Queue\nB) Heuristic function h(n)\nC) Stack\nD) Recursion"],
        "answer": "B",
        "explain": "A* uses f(n) = g(n) + h(n) where h(n) is the heuristic — makes it smarter than BFS!"
    },
    {
        "q": "Which Python method adds an item to the END of a list?",
        "options": ["A) insert()\nB) add()\nC) push()\nD) append()"],
        "answer": "D",
        "explain": "list.append(item) adds to the END. insert(0, item) adds at beginning."
    },
    {
        "q": "What is Edge AI?",
        "options": ["A) AI running only on cloud\nB) AI on local devices without cloud\nC) AI for gaming\nD) AI for networking only"],
        "answer": "B",
        "explain": "Edge AI = AI processing done locally on device (phone, sensor) — no cloud needed!"
    },
]

# Per-user quiz sessions
quiz_sessions = {}

# ================================================================
# HELPER FUNCTIONS
# ================================================================
def send_whatsapp(to, message):
    if not META_TOKEN or not META_PHONE_ID:
        print("ERROR: META_TOKEN or META_PHONE_ID not set!")
        return

    url = f"https://graph.facebook.com/v18.0/{META_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }

    # Split messages > 4000 chars
    if len(message) > 4000:
        parts = [message[i:i+3900] for i in range(0, len(message), 3900)]
        for part in parts:
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": part}
            }
            try:
                r = requests.post(url, headers=headers, json=data, timeout=10)
                print(f"Send response: {r.status_code} — {r.text}")
            except Exception as e:
                print(f"Send error: {e}")
    else:
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        try:
            r = requests.post(url, headers=headers, json=data, timeout=10)
            print(f"Send response: {r.status_code} — {r.text}")
        except Exception as e:
            print(f"Send error: {e}")

def call_groq(user_message):
    """Call Groq API with SVAI system prompt"""
    if not GROQ_API_KEY:
        return "❌ Groq API key not configured. Please set GROQ_API_KEY."

    system_prompt = """You are SVAI Assist, official WhatsApp Class Assistant Bot for BSc AI students at S.V. Arts College (Autonomous), TTD, Tirupati. Semester 2, Academic Year 2025-26. Built by P. Vinay, BSc AI 1st Year, Roll No: 2502321023.

RULES:
1. Always give helpful clear answers. Never refuse or say "I don't understand."
2. Keep responses under 300 words. Be concise.
3. Be friendly like a helpful senior student.
4. For exam questions give structured answers: Definition → Key Points → Example → Summary. End with: *All the best!* 🙏
5. For Python give short working code examples.
6. Format nicely for WhatsApp: use *bold*, bullet points.
7. Understand Telugu-English (Tenglish) perfectly.
8. If completely off-topic: redirect to HoD — 9670086068

COLLEGE: S.V. Arts College (Autonomous), TTD, Tirupati
COURSE : BSc AI, Semester 2, 2025-26
HOD    : Prof. K. Kameswara Rao — 9670086068"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 600,
        "temperature": 0.7
    }

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=data, timeout=15
        )
        result = resp.json()
        return result["choices"][0]["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        return "🌐 Internet error, try again!"
    except Exception as e:
        return f"⚠️ Error: {str(e)[:100]}\nContact HoD: 📞 9670086068"


def get_timetable_msg(day_key):
    """Format timetable for a given day"""
    if day_key not in TIMETABLE:
        return None
    tt = TIMETABLE[day_key]
    msg = f"📅 *{tt['day']} Timetable — BSc AI*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for period, subject in tt["periods"]:
        msg += f"🕐 *{period}*\n   {subject}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\nAll the best! 🙏"
    return msg


def get_today_timetable():
    """Get today's timetable based on current day"""
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    today = date.today().weekday()  # 0=Mon, 6=Sun
    if today == 6:
        return "📅 *Today is Sunday!*\n\nNo classes. Rest well! 😴\nSee you Monday! 🙏"
    day_key = day_names[today]
    return get_timetable_msg(day_key)


def find_student(query):
    """Search student by name, roll number (1-30), or full roll"""
    query = query.strip().lower()
    # Remove filler words
    for word in ["roll number", "roll no", "roll", "hall ticket", "student", "number", "no"]:
        query = query.replace(word, "").strip()
    query = query.strip()

    # Check if it's a full roll number (2502321XXX)
    full_roll_match = re.search(r'2502321(\d{3})', query)
    if full_roll_match:
        num = int(full_roll_match.group(1))
        if 1 <= num <= 30 and num in STUDENTS:
            return [(num, STUDENTS[num])]

    # Check if it's a number 1-30
    num_match = re.fullmatch(r'\d{1,2}', query)
    if num_match:
        num = int(query)
        if 1 <= num <= 30 and num in STUDENTS:
            return [(num, STUDENTS[num])]

    # Search by name (partial match)
    results = []
    for num, name in STUDENTS.items():
        if query in name.lower():
            results.append((num, name))
    return results


def format_student(num, name):
    return (
        f"🎫 *Student Found!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:* {name}\n"
        f"🔢 *Roll Number:* {roll_str(num)}\n"
        f"🎟️ *Hall Ticket:* {roll_str(num)}\n"
        f"📚 BSc AI, Sem 2, 2025-26\n"
        f"🏫 S.V. Arts College, Tirupati\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )


def get_all_students():
    msg = "👥 *All 30 Students — BSc AI 2025-26*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for num, name in STUDENTS.items():
        msg += f"{num:2}. {name} — {roll_str(num)}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n🏫 S.V. Arts College, Tirupati 🙏"
    return msg


def get_faculty_msg(search_term=None):
    """Return faculty info — specific or all"""
    if search_term:
        search_lower = search_term.lower()
        for f in FACULTY:
            for kw in f["keywords"]:
                if kw in search_lower:
                    return (
                        f"👨‍🏫 *Faculty Details*\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 *Name:* {f['name']}\n"
                        f"💼 *Role:* {f['role']}\n"
                        f"🎓 *Qual:* {f['qual']}\n"
                        f"📱 *Phone:* {f['phone']}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n🙏"
                    )

    # Return all faculty
    msg = "👨‍🏫 *CS Department Faculty*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for f in FACULTY:
        msg += f"👤 *{f['name']}*\n"
        msg += f"   💼 {f['role']}\n"
        msg += f"   📱 {f['phone']}\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n🙏 Contact HoD for queries: 9670086068"
    return msg


def get_lab_schedule():
    return (
        "🔬 *Lab Schedule — BSc AI Sem 2*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🧪 *Major Practical Lab*\n"
        "   📅 Monday: P1, P2, P3 (10AM–1PM)\n"
        "   📅 Saturday: P2, P3 (11AM–1PM)\n\n"
        "🧪 *Major 2 Practical*\n"
        "   📅 Tuesday: P4, P5 (2:15–4:15PM)\n\n"
        "🧪 *AI Skill Course Lab*\n"
        "   📅 Tuesday: P2 (11AM–12PM)\n"
        "   📅 Wednesday: P2 (11AM–12PM)\n"
        "   📅 Friday: P4 (2:15–3:15PM)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Room 206 = Computer Lab 🖥️\n"
        "All the best! 🙏"
    )


def get_countdown():
    today = date.today()
    mid1_start = date(2026, 3, 25)
    mid2_start = date(2026, 4, 24)
    sem_start  = date(2026, 5, 8)

    msg = "⏳ *Exam Countdown — BSc AI*\n━━━━━━━━━━━━━━━━━━━━━━\n"

    for name, exam_date in [("Mid-Term Exam I", mid1_start), ("Mid-Term Exam II", mid2_start), ("Semester Exam", sem_start)]:
        diff = (exam_date - today).days
        if diff < 0:
            msg += f"✅ *{name}* — Completed\n"
        elif diff == 0:
            msg += f"⚠️ *{name}* — TODAY! 😱\n"
        else:
            msg += f"📝 *{name}* — {diff} days left\n   ({exam_date.strftime('%d %b %Y')})\n\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📚 Start preparing early!\nAll the best! 🙏"
    return msg


def get_syllabus_msg(paper_num):
    """Get syllabus for paper 1, 2, or 3"""
    if paper_num not in SYLLABUS:
        return "❓ Please type *paper 1*, *paper 2*, or *paper 3* for syllabus."
    s = SYLLABUS[paper_num]
    msg = f"📚 *Paper {paper_num}: {s['title']}*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for unit_name, content in s["units"]:
        msg += f"\n📖 *{unit_name}*\n{content}\n"
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━\nAll the best! 🙏"
    return msg


def get_imp_questions_msg(paper_num, unit_num=None):
    """Get important questions"""
    if paper_num not in IMP_QUESTIONS:
        return "❓ Type *paper 1 questions*, *paper 2 questions*, or *paper 3 questions*."
    iq = IMP_QUESTIONS[paper_num]

    if unit_num and 1 <= unit_num <= 5:
        unit_name, content = iq["units"][unit_num - 1]
        msg = (
            f"📋 *Paper {paper_num} — {unit_name}*\n"
            f"*Important Questions*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{content}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"All the best! 🙏"
        )
    else:
        msg = (
            f"📋 *Paper {paper_num}: {iq['title']}*\n"
            f"*Important Questions — All Units*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⭐ *Top 5:* {iq['top5']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        for unit_name, content in iq["units"]:
            msg += f"📖 *{unit_name}*\n{content}\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\nAll the best! 🙏"
    return msg


def get_welcome():
    return (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🙏 *Om Namo Venkatesaya!*\n\n"
        "Welcome to *SVAI Assist* 🤖\n"
        "S.V. Arts College (Autonomous)\n"
        "BSc AI — Semester 2, 2025-26\n\n"
        "1️⃣ → Monday Timetable\n"
        "2️⃣ → Tuesday Timetable\n"
        "3️⃣ → Wednesday Timetable\n"
        "4️⃣ → Thursday Timetable\n"
        "5️⃣ → Friday Timetable\n"
        "6️⃣ → Saturday Timetable\n"
        "7️⃣ → Lab Schedule\n"
        "8️⃣ → Faculty Contacts\n"
        "9️⃣ → Exam Schedule\n"
        "🔟 → All Subjects List\n\n"
        "📘 *paper 1/2/3* → Syllabus\n"
        "📋 *paper 1/2/3 questions* → Imp Qs\n"
        "✏️ *explain <topic>* → Full answer\n\n"
        "🎫 Type your *name* → Roll number\n"
        "😂 *joke* | 🧠 *quiz* | ✨ *motivate*\n"
        "⏳ *countdown* | 🖥️ *code for <topic>*\n"
        "📅 *today* → Today's timetable\n\n"
        "Telugu also works! 🙏\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )


def get_subjects_list():
    return (
        "📚 *Subjects — BSc AI Semester 2*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📗 *Paper 1:* Python Programming & Data Structures\n"
        "📙 *Paper 2:* Artificial & Computational Intelligence\n"
        "📘 *Paper 3:* AI Skill Course — Applications of AI\n"
        "🔬 *Major 1:* Lab (Room 206)\n"
        "🔬 *Major 2:* Lab (Room 206)\n"
        "🇬🇧 *English* (Rooms 202/206/207)\n"
        "🔤 *Telugu / Sanskrit / Hindi* (Rooms 126/203/206)\n"
        "🌐 *MDC:* Multidisciplinary Course (Room 102/206)\n"
        "🏛️ *IKS:* Indian Knowledge Systems (Room 206)\n"
        "🎤 *Seminar* (Room 206)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "All the best! 🙏"
    )


def handle_quiz(phone, user_msg):
    """Handle quiz game flow"""
    msg_lower = user_msg.lower().strip()

    # Start new quiz
    if phone not in quiz_sessions or any(w in msg_lower for w in ["quiz", "start quiz", "test me", "mcq", "practice"]):
        import random
        selected = random.sample(QUIZ_QUESTIONS, min(5, len(QUIZ_QUESTIONS)))
        quiz_sessions[phone] = {
            "questions": selected,
            "current": 0,
            "score": 0,
            "total": len(selected),
            "active": True
        }
        session = quiz_sessions[phone]
        q = session["questions"][0]
        return (
            f"🧠 *SVAI Quiz Game!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"*Question 1/{session['total']}:*\n\n"
            f"{q['q']}\n\n"
            f"{q['options'][0]}\n\n"
            f"Type A, B, C, or D to answer! ✏️"
        )

    # Handle answer
    if phone in quiz_sessions and quiz_sessions[phone].get("active"):
        session = quiz_sessions[phone]
        answer = msg_lower.strip().upper()

        if answer not in ["A", "B", "C", "D"]:
            return "❓ Please type *A*, *B*, *C*, or *D* to answer!"

        current_idx = session["current"]
        q = session["questions"][current_idx]
        is_correct = (answer == q["answer"])

        if is_correct:
            session["score"] += 1
            feedback = f"✅ *Correct!* 🎉\n{q['explain']}"
        else:
            feedback = f"❌ *Wrong!* Correct answer: *{q['answer']}*\n{q['explain']}"

        session["current"] += 1

        if session["current"] >= session["total"]:
            # Quiz finished
            session["active"] = False
            score = session["score"]
            total = session["total"]
            if score == total:
                grade = "🌟 *Perfect Score! Outstanding!*"
            elif score >= total * 0.8:
                grade = "🏆 *Excellent! Keep it up!*"
            elif score >= total * 0.6:
                grade = "👍 *Good job! Study more!*"
            else:
                grade = "📚 *Need more practice!*"

            return (
                f"{feedback}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏁 *Quiz Complete!*\n"
                f"📊 Score: *{score}/{total}*\n"
                f"{grade}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Type *quiz* to play again! 🎮\n"
                f"All the best! 🙏"
            )
        else:
            # Next question
            next_q = session["questions"][session["current"]]
            return (
                f"{feedback}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"*Question {session['current']+1}/{session['total']}:*\n\n"
                f"{next_q['q']}\n\n"
                f"{next_q['options'][0]}\n\n"
                f"Type A, B, C, or D ✏️"
            )

    return None


def detect_paper_number(text):
    """Detect paper number from text"""
    text_lower = text.lower()
    if re.search(r'\bpaper\s*1\b|python|paper one|p1', text_lower):
        return "1"
    if re.search(r'\bpaper\s*2\b|artificial|intelligence|ai subject|paper two|p2', text_lower):
        return "2"
    if re.search(r'\bpaper\s*3\b|skill course|applications of ai|paper three|p3', text_lower):
        return "3"
    return None


def detect_unit_number(text):
    """Detect unit number from text"""
    match = re.search(r'unit\s*(\d)', text.lower())
    if match:
        return int(match.group(1))
    return None


# ================================================================
# MAIN MESSAGE HANDLER
# ================================================================

def handle_message(phone, text):
    """Main message router — handles all 20 features"""
    text_lower = text.lower().strip()
    original = text.strip()

    # ── FEATURE 1: Welcome / Help ──
    if any(w in text_lower for w in ["hi", "hello", "hey", "start", "help", "menu", "svai", "om namo", "welcome", "start bot"]):
        return get_welcome()

    # ── FEATURE 14: Quiz ──
    if any(w in text_lower for w in ["quiz", "start quiz", "test me", "mcq", "practice"]):
        return handle_quiz(phone, text_lower)

    # If quiz is active, handle answer
    if phone in quiz_sessions and quiz_sessions[phone].get("active"):
        if text_lower.upper() in ["A", "B", "C", "D"]:
            return handle_quiz(phone, text)

    # ── FEATURE 17: Exam Countdown ──
    if any(w in text_lower for w in ["countdown", "days left", "how many days", "enni rojulu", "enni days"]):
        return get_countdown()

    # ── FEATURE 6: Exam Schedule (check before timetable!) ──
    if any(w in text_lower for w in ["exam", "exam date", "internal", "semester exam", "mid term", "mid-1", "mid-2",
                                      "mid 1", "mid 2", "when is exam", "exam eppudu", "exam schedule",
                                      "exam time table", "exam timetable"]):
        return EXAM_SCHEDULE

    # ── FEATURE 2: Today's Timetable ──
    if any(w in text_lower for w in ["today", "today class", "today ki", "today lo enti", "emi undi today",
                                      "emi cheyali today", "aaj", "today timetable", "class today"]):
        return get_today_timetable()

    # ── FEATURE 2: Timetable by day name or number ──
    detected_day = None
    for alias, day_key in DAY_ALIASES.items():
        if alias in text_lower:
            detected_day = day_key
            break

    if detected_day is None:
        for num, day_key in DAY_NUMBER_MAP.items():
            if re.fullmatch(r'\s*' + num + r'\s*', original):
                detected_day = day_key
                break

    if detected_day:
        return get_timetable_msg(detected_day)

    # Generic timetable request (no day specified)
    if any(w in text_lower for w in ["timetable", "time table", "tt", "class schedule", "periods",
                                      "classes", "schedule", "timetable chupinchu"]):
        return (
            "📅 *Which day's timetable?*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Type the day name or number:\n"
            "1️⃣ Monday | 2️⃣ Tuesday\n"
            "3️⃣ Wednesday | 4️⃣ Thursday\n"
            "5️⃣ Friday | 6️⃣ Saturday\n"
            "📅 *today* → Today's classes"
        )

    # ── FEATURE 3: Lab Schedule (use word boundary — avoid matching 'lab' inside other words) ──
    lab_words = ["lab schedule", "lab day", "lab eppudu", "lab undi", "lab time",
                 "lab evvari", "practical", "pract", "which day lab", "lab days",
                 "lab today", "today lab"]
    # Only match standalone "lab" word, not when it's part of syllabus etc.
    is_lab_query = any(w in text_lower for w in lab_words) or \
                   bool(re.search(r'\blab\b', text_lower) and "syllabus" not in text_lower and "paper" not in text_lower)
    if is_lab_query:
        return get_lab_schedule()

    # ── FEATURE 5: Principal ──
    if any(w in text_lower for w in ["principal", "venugopal", "principal sir", "principal number",
                                      "principal evaru", "college head"]):
        return (
            f"🏫 *Principal Details*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Name:* {PRINCIPAL['name']}\n"
            f"💼 *Designation:* {PRINCIPAL['designation']}\n"
            f"🎓 *Qualification:* {PRINCIPAL['qual']}\n"
            f"📱 *Phone:* {PRINCIPAL['phone']}\n"
            f"🏫 S.V. Arts College (Autonomous), TTD, Tirupati\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n🙏"
        )

    # ── FEATURE 4: Faculty Contacts ──
    if any(w in text_lower for w in ["professor", "prof", "sir", "madam", "hod", "faculty", "contact",
                                      "number ichi", "sir number", "teacher", "lecturer",
                                      "kameswara", "jyotsna", "chakravarthy", "chennakesavulu",
                                      "kiranmayi", "sudha", "phone number", "all faculty"]):
        return get_faculty_msg(text_lower)

    # ── FEATURE 10: Subjects List ──
    if any(w in text_lower for w in ["subjects", "all subjects", "subject list", "which subjects",
                                      "papers", "subject names"]):
        return get_subjects_list()

    # ── FEATURE 11: Who Built SVAI ──
    if any(w in text_lower for w in ["who built", "who made", "evaru chesaru", "builder", "nuvvu evaru",
                                      "about bot", "who are you", "about svai", "vinay built", "created by"]):
        return (
            "🤖 *About SVAI Assist*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "👨‍💻 *Built By:* P. Vinay\n"
            "📚 *Course:* BSc AI, 1st Year\n"
            "🔢 *Roll No:* 2502321023\n"
            "🏫 *College:* S.V. Arts College (Autonomous)\n"
            "   TTD, Tirupati, AP\n\n"
            "🤖 *SVAI Assist* is your 24/7 class\n"
            "   assistant for BSc AI Sem 2!\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🙏 *Om Namo Venkatesaya!*"
        )

    # ── FEATURE 12: College Info ──
    if any(w in text_lower for w in ["college", "sv arts", "s.v. arts", "ttd", "about college",
                                      "college info", "college details"]):
        return (
            "🏫 *S.V. Arts College (Autonomous)*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📍 TTD, Tirupati, Andhra Pradesh\n"
            "🎓 B.Sc. Artificial Intelligence\n"
            "   Semester 2, Academic Year 2025-26\n\n"
            "👨‍💼 *Principal:* Prof. N. Venugopal Reddy\n"
            "📞 +91 90004 89182\n\n"
            "👨‍🏫 *HoD CS:* Prof. K. Kameswara Rao\n"
            "📞 9670086068\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🙏 *Om Namo Venkatesaya!*"
        )

    # ── FEATURE 13: Jokes ──
    if any(w in text_lower for w in ["joke", "funny", "navvinchu", "comedy", "haha", "lol", "hassu",
                                      "comedy cheppu", "navchai"]):
        idx = joke_index[0] % len(JOKES)
        joke_index[0] += 1
        return f"😂 *SVAI Joke!*\n━━━━━━━━━━━━━━━━━━━━━━\n{JOKES[idx]}\n━━━━━━━━━━━━━━━━━━━━━━\nType *joke* for another! 😄"

    # ── FEATURE 15: Motivation ──
    if any(w in text_lower for w in ["stress", "tension", "scared", "worried", "cant study", "can't study",
                                      "padalekapotunna", "chala kashtanga", "give up", "fail avutana",
                                      "time ledu", "motivate", "motivation", "padaledu", "depressed",
                                      "anxious", "nervous", "help me study", "study tips", "how to study"]):
        idx = motivation_index[0] % len(MOTIVATIONS)
        motivation_index[0] += 1
        return MOTIVATIONS[idx]

    # ── FEATURE 16: Study Timer ──
    if any(w in text_lower for w in ["timer", "pomodoro", "study timer", "25 min", "30 min", "focus timer"]):
        return (
            "⏱️ *Pomodoro Study Timer Tips*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🍅 *Pomodoro Technique:*\n"
            "📚 Study: 25 minutes\n"
            "☕ Break: 5 minutes\n"
            "🔄 Repeat 4 times → Long break 20 min\n\n"
            "⏰ *Use your phone timer:*\n"
            "• Android: Clock app → Timer\n"
            "• iPhone: Clock → Timer\n\n"
            "💡 *Tips:*\n"
            "• Phone on silent 📵\n"
            "• One subject at a time\n"
            "• Write notes by hand ✏️\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "All the best! 🙏"
        )

    # ── FEATURE 18: Python Quick Code ──
    code_match = re.search(
        r'code\s*for\s*(\w+)|syntax\s*of\s*(\w+)|show\s*me\s*code\s*(\w+)|example\s*of\s*(\w+)|'
        r'(\w+)\s*code|(\w+)\s*syntax|(\w+)\s*example|how\s*to\s*write\s*(\w+)',
        text_lower
    )
    if code_match:
        groups = [g for g in code_match.groups() if g]
        if groups:
            topic = groups[0].lower()
            for key in CODE_SNIPPETS:
                if key in topic or topic in key:
                    return (
                        f"🖥️ *Python Code: {topic.title()}*\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"{CODE_SNIPPETS[key]}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"All the best! 🙏"
                    )

    # ── FEATURE 9: Student Roll Number ──
    # Check for roll/student keywords OR just name/number lookup
    roll_keywords = ["roll number", "roll no", "roll", "hall ticket", "my roll", "na roll",
                     "roll marchipoya", "all students", "student list", "classmates",
                     "who is", "who is roll", "student"]
    is_roll_query = any(kw in text_lower for kw in roll_keywords)

    if "all students" in text_lower or "all roll" in text_lower or "student list" in text_lower or "classmates" in text_lower:
        return get_all_students()

    if is_roll_query or re.fullmatch(r'\d{1,2}', original.strip()) or re.search(r'2502321\d{3}', original):
        results = find_student(original)
        if results:
            if len(results) == 1:
                return format_student(results[0][0], results[0][1])
            else:
                msg = "🎫 *Multiple Students Found:*\n━━━━━━━━━━━━━━━━━━━━━━\n"
                for num, name in results:
                    msg += f"• {name} — {roll_str(num)}\n"
                msg += "━━━━━━━━━━━━━━━━━━━━━━\nType full name for details! 🙏"
                return msg
        elif is_roll_query:
            return "❓ Student not found!\nTry typing the name or number 1-30.\nType *all students* for full list! 📋"

    # ── FEATURE 8: Important Questions (check BEFORE syllabus to avoid conflict) ──
    imp_q_triggers = ["important question", "imp question", "imp q", "exam question",
                      "model paper", "most important", "questions cheppu", "guess paper",
                      "sure question", "important q", "imp qs", "expected question",
                      "questions for paper", "paper 1 question", "paper 2 question",
                      "paper 3 question", "unit question", "5 mark", "10 mark",
                      "5mark", "10mark", "sure q", "important topics"]
    if any(w in text_lower for w in imp_q_triggers):
        paper = detect_paper_number(text_lower)
        unit = detect_unit_number(text_lower)
        if paper:
            return get_imp_questions_msg(paper, unit)
        return (
            "📋 *Which paper's important questions?*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📗 *paper 1 questions* → Python\n"
            "📙 *paper 2 questions* → AI\n"
            "📘 *paper 3 questions* → AI Skill\n\n"
            "Or: *paper 1 unit 3 questions* for specific unit!\n"
            "Or: *paper 2 unit 1 questions* etc."
        )

    # ── FEATURE 7: Syllabus ──
    if any(w in text_lower for w in ["syllabus", "topics", "units", "portions", "sylly",
                                      "emi padali", "em vasthundi", "what to study", "portions cheppu"]):
        paper = detect_paper_number(text_lower)
        if paper:
            return get_syllabus_msg(paper)
        return (
            "📚 *Which paper's syllabus?*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "📗 *paper 1 syllabus* → Python\n"
            "📙 *paper 2 syllabus* → AI\n"
            "📘 *paper 3 syllabus* → AI Skill\n\n"
            "Type the paper number to continue!"
        )

    # ── Telugu greetings ──
    if any(w in text_lower for w in ["ela unnav", "ela unnaru", "how are you", "kaushalam", "bagunna"]):
        return (
            "🙏 *Baunnanu, meeru?* 😊\n\n"
            "Nenu SVAI Assist — mee class assistant! 🤖\n"
            "Mee questions ki ready ga unnanu!\n\n"
            "Type *menu* or *hi* for options! 📱"
        )

    # ── Tenglish: what class today ──
    if any(w in text_lower for w in ["emi undi", "emi class", "class undi aa", "today lo enti",
                                      "what class", "evariki class"]):
        return get_today_timetable()

    # ── FEATURE 19 + 20: Groq AI for everything else ──
    # Detect if it's likely an exam/subject question
    ai_keywords = ["explain", "define", "what is", "what are", "describe", "discuss",
                   "difference between", "compare", "types of", "cheppu", "artham",
                   "easy ga cheppu", "example ivvu", "example", "how does", "write about",
                   "tell me about", "advantages", "disadvantages", "applications",
                   "bfs", "dfs", "peas", "stack", "queue", "linked list", "inheritance",
                   "encapsulation", "polymorphism", "oop", "machine learning", "deep learning",
                   "neural network", "fuzzy", "a star", "a*", "algorithm", "data structure",
                   "python", "function", "loop", "class", "object", "recursion",
                   "supervised", "unsupervised", "reinforcement", "clustering", "regression",
                   "edge ai", "cloud ai", "vibe coding", "data pipeline", "kaggle",
                   "expert system", "knowledge base", "inference engine"]

    if any(w in text_lower for w in ai_keywords):
        return call_groq(original)

    # ── Name search (fallback for student lookup by typing name) ──
    name_results = find_student(original)
    if name_results and len(original.split()) <= 3:
        if len(name_results) == 1:
            return format_student(name_results[0][0], name_results[0][1])
        elif len(name_results) > 1:
            msg = "🎫 *Students Found:*\n━━━━━━━━━━━━━━━━━━━━━━\n"
            for num, name in name_results:
                msg += f"• {name} — {roll_str(num)}\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━━\nType full name for details!"
            return msg

    # ── FINAL FALLBACK: Groq AI ──
    return call_groq(original)


# ================================================================
# FLASK ROUTES
# ================================================================

@app.route("/", methods=["GET"])
def home():
    return "🤖 SVAI Assist is LIVE! Om Namo Venkatesaya! 🙏", 200


@app.route("/ping", methods=["GET"])
def ping():
    """Uptime Robot keep-alive endpoint"""
    return "pong", 200


@app.route("/health", methods=["GET"])
def health():
    """Render health check"""
    return jsonify({"status": "ok", "bot": "SVAI Assist", "college": "S.V. Arts College Tirupati"}), 200


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Meta webhook verification"""
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print(f"✅ Webhook verified!")
        return challenge, 200
    print(f"❌ Webhook verification failed. Token: {token}")
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def receive_message():
    """Receive and reply to WhatsApp messages"""
    try:
        data = request.get_json()

        if not data:
            return "OK", 200

        # Navigate to message
        entry = data.get("entry", [])
        if not entry:
            return "OK", 200

        changes = entry[0].get("changes", [])
        if not changes:
            return "OK", 200

        value = changes[0].get("value", {})

        # Only process if there's a message (not status updates)
        if "messages" not in value:
            return "OK", 200

        messages = value["messages"]
        if not messages:
            return "OK", 200

        message = messages[0]

        # Only handle text messages
        if message.get("type") != "text":
            return "OK", 200

        phone = message["from"]
        text  = message["text"]["body"]

        print(f"📨 Message from {phone}: {text}")

        # Generate reply
        reply = handle_message(phone, text)

        # Send reply
        send_whatsapp(phone, reply)

        print(f"✅ Replied to {phone}")

    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")

    # Always return 200 to Meta
    return "OK", 200


# ================================================================
# MAIN
# ================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
