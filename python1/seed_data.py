import sys
from datetime import datetime, timedelta
import json
from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.course import Course
from app.models.lesson import Module, Lesson
from app.models.progress import Enrollment, LessonProgress
from app.models.assessment import Assessment, Question, AssessmentResult
from app.services.auth_service import get_password_hash

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def seed():
    print("=" * 60)
    print("[*] Starting EduPulse Database Seeding...")
    print("=" * 60)

    # Recreate tables to ensure clean slate
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Check if already seeded
        existing_admin = db.query(User).filter(User.email == "admin@elearning.com").first()
        if existing_admin:
            print("[!] Database already has seed data. Cleaning up old records to re-seed fresh...")
            db.query(AssessmentResult).delete()
            db.query(LessonProgress).delete()
            db.query(Enrollment).delete()
            db.query(Question).delete()
            db.query(Assessment).delete()
            db.query(Lesson).delete()
            db.query(Module).delete()
            db.query(Course).delete()
            db.query(User).delete()
            db.commit()

        # 2. Users
        print("[*] Creating Admin and Student accounts...")
        admin = User(
            name="Administrator",
            email="admin@elearning.com",
            password_hash=get_password_hash("admin123"),
            role="admin",
            bio="Lead Platform Architect & Curriculum Director at EduPulse.",
            created_at=datetime.utcnow() - timedelta(days=60)
        )
        db.add(admin)

        student = User(
            name="Demo Student",
            email="student@elearning.com",
            password_hash=get_password_hash("student123"),
            role="student",
            bio="Software engineering student passionate about systems design and algorithms.",
            preferred_resource_type="Practice",
            created_at=datetime.utcnow() - timedelta(days=30)
        )
        db.add(student)

        # Additional realistic students for directory & analytics
        extra_students = [
            User(name="Sarah Chen", email="sarah.chen@example.com", password_hash=get_password_hash("pass123"), role="student", bio="Junior backend engineer leveling up in DBMS & Python.", preferred_resource_type="Video", created_at=datetime.utcnow() - timedelta(days=25)),
            User(name="Marcus Patel", email="marcus.p@example.com", password_hash=get_password_hash("pass123"), role="student", bio="Computer Science senior focusing on technical interview prep.", preferred_resource_type="Practice", created_at=datetime.utcnow() - timedelta(days=20)),
            User(name="Elena Rostova", email="elena.r@example.com", password_hash=get_password_hash("pass123"), role="student", bio="Data analyst transitioning to data engineering.", preferred_resource_type="Article", created_at=datetime.utcnow() - timedelta(days=15)),
            User(name="David Kim", email="david.kim@example.com", password_hash=get_password_hash("pass123"), role="student", bio="Frontend dev branching into full-stack FastAPI architectures.", preferred_resource_type="Mixed", created_at=datetime.utcnow() - timedelta(days=10)),
        ]
        for s in extra_students:
            db.add(s)

        db.commit()
        db.refresh(student)

        # 3. Courses, Modules, Lessons, Assessments
        courses_data = [
            {
                "title": "Python Programming: Fundamentals to Production",
                "description": "Comprehensive journey from foundational Python syntax to object-oriented architecture, decorators, context managers, and async concurrency.",
                "category": "Python Programming",
                "difficulty": "Beginner",
                "duration": "8 hours",
                "instructor": "Dr. Sarah Jenkins",
                "thumbnail": "",
                "rating": 4.9,
                "learning_objectives": "Master core data structures (lists, tuples, dicts, sets)\nWrite robust object-oriented classes and inheritance hierarchies\nImplement advanced Python decorators and context managers\nBuild structured, maintainable Python applications",
                "modules": [
                    {
                        "title": "Module 1 — Python Fundamentals",
                        "description": "Core syntax, variables, primitive types, and operators.",
                        "lessons": [
                            {
                                "title": "Introduction to Python & Execution Environment",
                                "duration": "15 mins",
                                "video_url": "https://www.youtube.com/watch?v=kqtD5dpn9C8",
                                "resource_url": "https://docs.python.org/3/tutorial/interpreter.html",
                                "content": """<h2>Welcome to Python</h2>
<p>Python is a high-level, interpreted programming language created by Guido van Rossum. Known for its clarity, clean readable syntax, and extensive standard library, Python powers modern backend architectures, data science pipelines, and automated tooling worldwide.</p>
<div class="code-block">
# Printing your first message
print("Hello, EduPulse World!")

# Dynamic typing demonstration
x = 42
print(f"Value: {x}, Type: {type(x)}")
</div>
<h3>Why Python in Production?</h3>
<ul>
  <li><strong>Readability:</strong> Code is read vastly more often than it is written.</li>
  <li><strong>Rich Ecosystem:</strong> Package repositories like PyPI provide battle-tested frameworks like FastAPI and SQLAlchemy.</li>
  <li><strong>Batteries Included:</strong> Built-in math, file IO, JSON serialization, and networking primitives.</li>
</ul>"""
                            },
                            {
                                "title": "Variables, Primitive Types & Type Casting",
                                "duration": "20 mins",
                                "video_url": "https://www.youtube.com/watch?v=cQT33yu9pY8",
                                "resource_url": "https://docs.python.org/3/library/stdtypes.html",
                                "content": """<h2>Understanding Python Primitives</h2>
<p>In Python, everything is an object. Variables are references (pointers) to objects stored in memory. The core scalar primitives include:</p>
<ul>
  <li><code>int</code>: Arbitrary-precision integers</li>
  <li><code>float</code>: 64-bit IEEE 754 floating-point numbers</li>
  <li><code>str</code>: Immutable sequence of Unicode code points</li>
  <li><code>bool</code>: Boolean subtype of integer (<code>True</code> or <code>False</code>)</li>
</ul>
<div class="code-block">
user_age: int = 24
account_balance: float = 1250.75
user_name: str = "Alice"
is_verified: bool = True

# Type casting
age_str = str(user_age)
print(f"User {user_name} has balance ${account_balance:.2f}")
</div>"""
                            },
                            {
                                "title": "Operators, Truthiness & Expressions",
                                "duration": "18 mins",
                                "video_url": "",
                                "resource_url": "https://docs.python.org/3/reference/expressions.html",
                                "content": """<h2>Arithmetic & Logical Expressions</h2>
<p>Python provides comprehensive arithmetic, comparison, and boolean logical operators.</p>
<div class="code-block">
a = 15
b = 4

print("Division:", a / b)       # 3.75 (float)
print("Floor Division:", a // b) # 3 (int)
print("Modulo:", a % b)         # 3
print("Exponentiation:", a ** b) # 50625

# Short-circuit logic
is_admin = True
has_permission = False
can_edit = is_admin or has_permission
print("Can edit:", can_edit)
</div>"""
                            }
                        ]
                    },
                    {
                        "title": "Module 2 — Control Flow & Iteration",
                        "description": "Conditional branching, loops, and comprehensions.",
                        "lessons": [
                            {
                                "title": "Conditional Statements: if, elif, and else",
                                "duration": "15 mins",
                                "video_url": "",
                                "resource_url": "https://docs.python.org/3/tutorial/controlflow.html",
                                "content": """<h2>Branching Execution Paths</h2>
<p>Conditionals allow programs to execute specific blocks based on boolean predicate evaluations.</p>
<div class="code-block">
score = 85

if score >= 90:
    grade = 'A'
elif score >= 80:
    grade = 'B'
elif score >= 70:
    grade = 'C'
else:
    grade = 'F'

print(f"Assigned Grade: {grade}")
</div>"""
                            },
                            {
                                "title": "For Loops, While Loops & Comprehensions",
                                "duration": "25 mins",
                                "video_url": "https://www.youtube.com/watch?v=6iF8Xb7Z3wQ",
                                "resource_url": "https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions",
                                "content": """<h2>Idiomatic Iteration in Python</h2>
<p>Python emphasizes iterable sequences and list comprehensions over traditional index-based iteration counters.</p>
<div class="code-block">
# Iterating over collections
fruits = ["apple", "banana", "cherry"]
for index, fruit in enumerate(fruits, start=1):
    print(f"{index}. {fruit.capitalize()}")

# Modern List Comprehension
squares = [x ** 2 for x in range(1, 11) if x % 2 == 0]
print("Even Squares:", squares) # [4, 16, 36, 64, 100]
</div>"""
                            }
                        ]
                    },
                    {
                        "title": "Module 3 — Functions & Modular Architecture",
                        "description": "Function definitions, parameters, return types, and scope.",
                        "lessons": [
                            {
                                "title": "Defining Functions, *args, and **kwargs",
                                "duration": "22 mins",
                                "video_url": "https://www.youtube.com/watch?v=9Os0o3wzS_I",
                                "resource_url": "https://docs.python.org/3/tutorial/controlflow.html#defining-functions",
                                "content": """<h2>Designing Reusable Functions</h2>
<p>Functions encapsulate business logic and enable clean modular code organization.</p>
<div class="code-block">
def calculate_tax(subtotal: float, tax_rate: float = 0.08) -> float:
    \"\"\"Calculates applicable tax on a transaction.\"\"\"
    return round(subtotal * tax_rate, 2)

def log_event(event_name: str, *tags, **metadata):
    print(f"[EVENT] {event_name}")
    print(f"Tags: {tags}")
    print(f"Metadata: {metadata}")

log_event("user_login", "security", "auth", user_id=101, ip="127.0.0.1")
</div>"""
                            }
                        ]
                    }
                ],
                "assessment": {
                    "title": "Python Programming Fundamentals Assessment",
                    "description": "Test your grasp on core Python data types, loops, list comprehensions, and function signatures.",
                    "pass_percentage": 70.0,
                    "questions": [
                        {
                            "question_text": "What is the output of `type([])` in Python 3?",
                            "option_a": "<class 'array'>",
                            "option_b": "<class 'list'>",
                            "option_c": "<class 'tuple'>",
                            "option_d": "<class 'collection'>",
                            "correct_option": "B",
                            "explanation": "In Python, square brackets [] define a built-in list object, which belongs to the class 'list'."
                        },
                        {
                            "question_text": "Which of the following creates an empty set in Python?",
                            "option_a": "{}",
                            "option_b": "set()",
                            "option_c": "[]",
                            "option_d": "dict()",
                            "correct_option": "B",
                            "explanation": "{} creates an empty dictionary in Python. To initialize an empty set, you must use the set() constructor."
                        },
                        {
                            "question_text": "What is the evaluated output of the expression `[x * 2 for x in range(3)]`?",
                            "option_a": "[0, 2, 4]",
                            "option_b": "[2, 4, 6]",
                            "option_c": "[1, 2, 3]",
                            "option_d": "[0, 1, 2]",
                            "correct_option": "A",
                            "explanation": "range(3) produces numbers 0, 1, 2. Multiplying each by 2 yields [0, 2, 4]."
                        },
                        {
                            "question_text": "What does the floor division operator `//` return when dividing 7 by 2?",
                            "option_a": "3.5",
                            "option_b": "3",
                            "option_c": "4",
                            "option_d": "1",
                            "correct_option": "B",
                            "explanation": "The floor division operator (//) truncates down to the nearest integer. 7 // 2 results in integer 3."
                        },
                        {
                            "question_text": "In Python function parameters, what does `**kwargs` capture?",
                            "option_a": "A tuple of positional arguments",
                            "option_b": "A dictionary of keyword arguments",
                            "option_c": "A list of required strings",
                            "option_d": "A pointer to memory",
                            "correct_option": "B",
                            "explanation": "**kwargs captures arbitrary named keyword arguments passed to a function into a standard Python dictionary."
                        }
                    ]
                }
            },
            {
                "title": "Data Structures & Algorithms in Practice",
                "description": "Master algorithmic complexity (Big-O), arrays, linked lists, trees, graphs, sorting algorithms, and dynamic programming.",
                "category": "Data Structures",
                "difficulty": "Intermediate",
                "duration": "10 hours",
                "instructor": "Prof. Alan Vance",
                "thumbnail": "",
                "rating": 4.8,
                "learning_objectives": "Calculate time and space complexity with Big-O notation\nImplement linear data structures: Linked Lists, Stacks, Queues\nMaster hierarchical trees: Binary Search Trees and Heaps\nSolve algorithmic problems using recursion and Dynamic Programming",
                "modules": [
                    {
                        "title": "Module 1 — Asymptotic Analysis & Arrays",
                        "description": "Understanding Big-O notation and contiguous memory data structures.",
                        "lessons": [
                            {
                                "title": "Big-O Notation: Time and Space Complexity",
                                "duration": "25 mins",
                                "video_url": "https://www.youtube.com/watch?v=kS_JgGzE8MQ",
                                "resource_url": "https://en.wikipedia.org/wiki/Big_O_notation",
                                "content": """<h2>Asymptotic Analysis</h2>
<p>Big-O notation describes the upper bound of execution time or memory utilization as the input size <code>N</code> scales towards infinity.</p>
<ul>
  <li><code>O(1)</code>: Constant Time — Hash map lookups, array index access</li>
  <li><code>O(log N)</code>: Logarithmic Time — Binary Search</li>
  <li><code>O(N)</code>: Linear Time — Single loop through an array</li>
  <li><code>O(N log N)</code>: Linearithmic Time — Merge Sort, Quick Sort (average)</li>
  <li><code>O(N²)</code>: Quadratic Time — Nested loops, Bubble Sort</li>
</ul>"""
                            },
                            {
                                "title": "Dynamic Arrays & Amortized Analysis",
                                "duration": "20 mins",
                                "video_url": "",
                                "resource_url": "",
                                "content": """<h2>How Dynamic Arrays Function</h2>
<p>A static array has a fixed capacity in contiguous memory. A dynamic array allocates an underlying fixed array. When filled to capacity, it allocates a new buffer of 2x size and copies existing elements.</p>
<div class="code-block">
class DynamicArray:
    def __init__(self):
        self.capacity = 2
        self.length = 0
        self.arr = [None] * self.capacity

    def push(self, val):
        if self.length == self.capacity:
            self.resize()
        self.arr[self.length] = val
        self.length += 1

    def resize(self):
        self.capacity *= 2
        new_arr = [None] * self.capacity
        for i in range(self.length):
            new_arr[i] = self.arr[i]
        self.arr = new_arr
</div>"""
                            }
                        ]
                    },
                    {
                        "title": "Module 2 — Linked Lists, Stacks & Queues",
                        "description": "Pointer-linked nodes and LIFO/FIFO patterns.",
                        "lessons": [
                            {
                                "title": "Singly & Doubly Linked Lists",
                                "duration": "22 mins",
                                "video_url": "",
                                "resource_url": "",
                                "content": """<h2>Linked Lists</h2>
<p>A Linked List consists of distinct node structures containing a data payload and a pointer reference to the next node in sequence.</p>
<div class="code-block">
class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    def prepend(self, value):
        new_node = Node(value)
        new_node.next = self.head
        self.head = new_node
</div>"""
                            }
                        ]
                    },
                    {
                        "title": "Module 3 — Tree Data Structures & Traversals",
                        "description": "Binary Search Trees, In-Order, Pre-Order, and Post-Order traversal.",
                        "lessons": [
                            {
                                "title": "Binary Search Trees (BST) & Search Complexity",
                                "duration": "30 mins",
                                "video_url": "https://www.youtube.com/watch?v=f5dU3xoEPaA",
                                "resource_url": "",
                                "content": """<h2>Binary Search Tree Invariant</h2>
<p>For any node <code>N</code> in a Binary Search Tree:</p>
<ul>
  <li>All keys in node <code>N</code>'s left subtree are strictly less than <code>N.key</code></li>
  <li>All keys in node <code>N</code>'s right subtree are strictly greater than <code>N.key</code></li>
</ul>
<p>Average search, insertion, and deletion complexity is <code>O(log N)</code> in balanced trees.</p>"""
                            }
                        ]
                    }
                ],
                "assessment": {
                    "title": "Data Structures & Complexity Exam",
                    "description": "Evaluate understanding of Big-O analysis, stack/queue behaviors, and tree invariants.",
                    "pass_percentage": 70.0,
                    "questions": [
                        {
                            "question_text": "What is the average time complexity of searching an element in a balanced Binary Search Tree (BST)?",
                            "option_a": "O(1)",
                            "option_b": "O(log N)",
                            "option_c": "O(N)",
                            "option_d": "O(N log N)",
                            "correct_option": "B",
                            "explanation": "In a balanced binary search tree, half of the search space is eliminated at each step, yielding O(log N) average time complexity."
                        },
                        {
                            "question_text": "Which data structure operates strictly on a Last-In, First-Out (LIFO) protocol?",
                            "option_a": "Queue",
                            "option_b": "Stack",
                            "option_c": "Priority Queue",
                            "option_d": "Array",
                            "correct_option": "B",
                            "explanation": "A Stack operates on a LIFO basis: the element pushed last is the first to be popped off."
                        },
                        {
                            "question_text": "What is the worst-case time complexity of Quick Sort?",
                            "option_a": "O(N log N)",
                            "option_b": "O(N²)",
                            "option_c": "O(N)",
                            "option_d": "O(log N)",
                            "correct_option": "B",
                            "explanation": "When an unbalanced pivot is repeatedly chosen (such as the smallest or largest item on an already sorted array), Quick Sort degrades to O(N²)."
                        },
                        {
                            "question_text": "What is the time complexity of looking up a key in a standard Hash Map with good hash distribution?",
                            "option_a": "O(1) average",
                            "option_b": "O(log N)",
                            "option_c": "O(N)",
                            "option_d": "O(N²)",
                            "correct_option": "A",
                            "explanation": "Hash maps use direct array index addressing derived from hash codes, providing O(1) average time lookups."
                        },
                        {
                            "question_text": "Which tree traversal algorithm visits nodes in the order: Left Subtree, Root, Right Subtree?",
                            "option_a": "Pre-Order",
                            "option_b": "In-Order",
                            "option_c": "Post-Order",
                            "option_d": "Breadth-First",
                            "correct_option": "B",
                            "explanation": "In-Order traversal processes the left child, then the parent (root), then the right child, which prints BST elements in sorted ascending order."
                        }
                    ]
                }
            },
            {
                "title": "Database Management Systems & SQL Mastery",
                "description": "Relational database modeling, SQL querying, indexing, ACID transactions, normalization, and SQLAlchemy ORM patterns.",
                "category": "Database Management",
                "difficulty": "Intermediate",
                "duration": "7 hours",
                "instructor": "Marcus Sterling",
                "thumbnail": "",
                "rating": 4.9,
                "learning_objectives": "Design normalized schemas up to 3rd Normal Form (3NF)\nWrite complex SQL joins, aggregations, and subqueries\nOptimize query execution plans with B-Tree indexes\nUnderstand ACID guarantees and isolation levels",
                "modules": [
                    {
                        "title": "Module 1 — Relational Modeling & Schema Design",
                        "description": "Tables, keys, constraints, and normalization.",
                        "lessons": [
                            {
                                "title": "Primary Keys, Foreign Keys & Constraints",
                                "duration": "18 mins",
                                "video_url": "https://www.youtube.com/watch?v=HXV3zeQKqGY",
                                "resource_url": "https://www.postgresql.org/docs/current/ddl-constraints.html",
                                "content": """<h2>Relational Data Modeling</h2>
<p>Relational databases structure data into tables composed of rows (tuples) and columns (attributes).</p>
<ul>
  <li><strong>Primary Key (PK):</strong> Unique, non-null identifier for a row.</li>
  <li><strong>Foreign Key (FK):</strong> Enforces referential integrity linking a child record to its parent.</li>
  <li><strong>CASCADE:</strong> Automatic deletion of orphaned child rows when parent is deleted.</li>
</ul>
<div class="code-block">
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(150) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INT NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
</div>"""
                            },
                            {
                                "title": "Normalization: 1NF, 2NF, and 3NF",
                                "duration": "25 mins",
                                "video_url": "",
                                "resource_url": "",
                                "content": """<h2>Database Normalization Principles</h2>
<p>Normalization reduces data redundancy and prevents insertion, update, and deletion anomalies.</p>
<ul>
  <li><strong>1NF (First Normal Form):</strong> Atomic values per cell, unique rows.</li>
  <li><strong>2NF (Second Normal Form):</strong> In 1NF and no partial dependencies on composite keys.</li>
  <li><strong>3NF (Third Normal Form):</strong> In 2NF and no transitive functional dependencies.</li>
</ul>"""
                            }
                        ]
                    },
                    {
                        "title": "Module 2 — Advanced SQL Queries & Joins",
                        "description": "Inner, Left, and Outer Joins, Group By, and Window Functions.",
                        "lessons": [
                            {
                                "title": "SQL Joins, Aggregations & Grouping",
                                "duration": "30 mins",
                                "video_url": "https://www.youtube.com/watch?v=9yeOJ0ZMUYw",
                                "resource_url": "",
                                "content": """<h2>Mastering SQL Joins</h2>
<div class="code-block">
-- Querying total enrollments per course category
SELECT 
    c.category,
    COUNT(e.id) AS total_enrollments,
    ROUND(AVG(c.rating), 2) AS average_rating
FROM courses c
LEFT JOIN enrollments e ON c.id = e.course_id
GROUP BY c.category
HAVING COUNT(e.id) > 0
ORDER BY total_enrollments DESC;
</div>"""
                            }
                        ]
                    },
                    {
                        "title": "Module 3 — Transactions & Indexing",
                        "description": "ACID properties, B-Tree indexes, and Query optimization.",
                        "lessons": [
                            {
                                "title": "ACID Properties & Transaction Isolation",
                                "duration": "22 mins",
                                "video_url": "",
                                "resource_url": "",
                                "content": """<h2>The ACID Guarantees</h2>
<ul>
  <li><strong>Atomicity:</strong> All operations in a transaction succeed, or the entire transaction rolls back.</li>
  <li><strong>Consistency:</strong> Transactions transition the database from one valid state to another.</li>
  <li><strong>Isolation:</strong> Concurrent transactions execute without dirty read interferences.</li>
  <li><strong>Durability:</strong> Once committed, transaction effects persist even through system crashes.</li>
</ul>"""
                            }
                        ]
                    }
                ],
                "assessment": {
                    "title": "Database Systems & SQL Assessment",
                    "description": "Validate database schema design, join syntax, normalization rules, and ACID concepts.",
                    "pass_percentage": 70.0,
                    "questions": [
                        {
                            "question_text": "What does the 'A' in ACID transaction guarantees represent?",
                            "option_a": "Availability",
                            "option_b": "Atomicity",
                            "option_c": "Authentication",
                            "option_d": "Asynchronous",
                            "correct_option": "B",
                            "explanation": "ACID stands for Atomicity, Consistency, Isolation, and Durability."
                        },
                        {
                            "question_text": "Which SQL JOIN returns all rows from the left table and matched rows from the right table?",
                            "option_a": "INNER JOIN",
                            "option_b": "LEFT JOIN",
                            "option_c": "RIGHT JOIN",
                            "option_d": "CROSS JOIN",
                            "correct_option": "B",
                            "explanation": "A LEFT JOIN preserves every row from the left table, populating NULL for right table columns when no match exists."
                        },
                        {
                            "question_text": "What is the primary objective of Database Normalization?",
                            "option_a": "Increase disk consumption",
                            "option_b": "Eliminate redundant data and prevent modification anomalies",
                            "option_c": "Encrypt confidential records",
                            "option_d": "Disable foreign key constraints",
                            "correct_option": "B",
                            "explanation": "Normalization organizes schema tables to minimize duplicate data and eliminate update/deletion anomalies."
                        },
                        {
                            "question_text": "Which index data structure is predominantly used by relational database engines (PostgreSQL, MySQL, SQLite)?",
                            "option_a": "Binary Heap",
                            "option_b": "B-Tree (Balanced Tree)",
                            "option_c": "Linked List",
                            "option_d": "Stack",
                            "correct_option": "B",
                            "explanation": "B-Trees and B+ Trees allow efficient logarithmic searches, range queries, and sequential traversals on disk blocks."
                        },
                        {
                            "question_text": "In SQL, which clause filters aggregated rows produced by a GROUP BY statement?",
                            "option_a": "WHERE",
                            "option_b": "HAVING",
                            "option_c": "ORDER BY",
                            "option_d": "LIMIT",
                            "correct_option": "B",
                            "explanation": "WHERE filters rows prior to aggregation, while HAVING filters group aggregations (e.g. HAVING COUNT(*) > 5)."
                        }
                    ]
                }
            },
            {
                "title": "Modern Web Development with FastAPI & REST Architecture",
                "description": "Architect high-performance APIs with Python, FastAPI, Pydantic data validation, JWT authentication, and responsive client-side UI.",
                "category": "Web Development",
                "difficulty": "Intermediate",
                "duration": "9 hours",
                "instructor": "Elena Cruz",
                "thumbnail": "",
                "rating": 4.9,
                "learning_objectives": "Build production REST APIs with FastAPI routing and OpenAPI docs\nValidate request and response schemas with Pydantic v2\nImplement secure JWT token authorization and password hashing\nStructure scalable multi-layer web architectures",
                "modules": [
                    {
                        "title": "Module 1 — REST Principles & FastAPI Architecture",
                        "description": "HTTP methods, status codes, and routing.",
                        "lessons": [
                            {
                                "title": "REST Architecture & HTTP Semantics",
                                "duration": "20 mins",
                                "video_url": "https://www.youtube.com/watch?v=0sOvCWFmrtA",
                                "resource_url": "https://fastapi.tiangolo.com/",
                                "content": """<h2>Modern API Architecture</h2>
<p>Representational State Transfer (REST) leverages HTTP methods to operate on web resources:</p>
<ul>
  <li><code>GET</code>: Safe, idempotent retrieval</li>
  <li><code>POST</code>: Non-idempotent creation</li>
  <li><code>PUT / PATCH</code>: Full / Partial resource mutation</li>
  <li><code>DELETE</code>: Resource removal</li>
</ul>
<div class="code-block">
from fastapi import FastAPI

app = FastAPI(title="EduPulse API")

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}
</div>"""
                            },
                            {
                                "title": "Pydantic Schemas & Request Validation",
                                "duration": "24 mins",
                                "video_url": "",
                                "resource_url": "https://docs.pydantic.dev/",
                                "content": """<h2>Strict Data Validation with Pydantic</h2>
<p>Pydantic enforces strict type safety, data parsing, and auto-generates JSON Schema specifications.</p>
<div class="code-block">
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
</div>"""
                            }
                        ]
                    },
                    {
                        "title": "Module 2 — Authentication & Security",
                        "description": "Bcrypt hashing, JWT bearer tokens, and route protection.",
                        "lessons": [
                            {
                                "title": "Password Hashing & JWT Bearer Tokens",
                                "duration": "28 mins",
                                "video_url": "",
                                "resource_url": "https://jwt.io/",
                                "content": """<h2>Production Security Patterns</h2>
<p>Never store plain-text passwords. Use adaptive hashing (bcrypt) and issue stateless JSON Web Tokens containing cryptographically verified claims.</p>
<div class="code-block">
# JWT Structure
Header.Payload.Signature
# Stored securely in HttpOnly cookies or Bearer Authorization headers
</div>"""
                            }
                        ]
                    },
                    {
                        "title": "Module 3 — Full-Stack Integration",
                        "description": "Jinja2 server templating, asynchronous fetch requests, and responsive CSS.",
                        "lessons": [
                            {
                                "title": "Server-Rendered UI with Jinja2 & Dynamic JavaScript",
                                "duration": "25 mins",
                                "video_url": "",
                                "resource_url": "https://jinja.palletsprojects.com/",
                                "content": """<h2>Modern Server-Driven Web UI</h2>
<p>Combining FastAPI, Jinja2 templating, and Vanilla JavaScript provides instant page loads, SEO optimization, and clean interactive client experiences without massive frontend framework overhead.</p>"""
                            }
                        ]
                    }
                ],
                "assessment": {
                    "title": "Web Architecture & API Security Exam",
                    "description": "Assess your understanding of REST methods, HTTP status codes, JWT tokens, and Pydantic validation.",
                    "pass_percentage": 70.0,
                    "questions": [
                        {
                            "question_text": "Which HTTP status code signifies that a new resource has been successfully created?",
                            "option_a": "200 OK",
                            "option_b": "201 Created",
                            "option_c": "204 No Content",
                            "option_d": "301 Moved Permanently",
                            "correct_option": "B",
                            "explanation": "201 Created is the standard HTTP status indicating that the request succeeded and a new resource was provisioned."
                        },
                        {
                            "question_text": "Why should password hashes be generated with a cryptographic salt?",
                            "option_a": "To reduce hash length",
                            "option_b": "To defend against rainbow table lookups",
                            "option_c": "To convert the password to plain-text",
                            "option_d": "To avoid using CPU power",
                            "correct_option": "B",
                            "explanation": "A unique cryptographic salt ensures identical passwords produce distinct hashes, neutralizing precomputed rainbow table attacks."
                        },
                        {
                            "question_text": "Which component of a JWT ensures that its payload has not been tampered with?",
                            "option_a": "The Header",
                            "option_b": "The Cryptographic Signature",
                            "option_c": "The JSON formatting",
                            "option_d": "The Base64 encoding",
                            "correct_option": "B",
                            "explanation": "The signature is generated using the secret key; any modification to the header or payload invalidates the signature."
                        },
                        {
                            "question_text": "What does Pydantic do when incoming request data fails field validation rules?",
                            "option_a": "Silently substitutes empty values",
                            "option_b": "Raises a ValidationError and returns HTTP 422 Unprocessable Entity",
                            "option_c": "Crashes the server process",
                            "option_d": "Redirects to the home page",
                            "correct_option": "B",
                            "explanation": "FastAPI and Pydantic automatically return a structured 422 Unprocessable Entity response specifying exactly which fields failed validation."
                        },
                        {
                            "question_text": "Which HTTP method is defined as idempotent according to RFC specifications?",
                            "option_a": "POST",
                            "option_b": "PUT",
                            "option_c": "CONNECT",
                            "option_d": "PATCH (when appending)",
                            "correct_option": "B",
                            "explanation": "PUT is idempotent: executing identical PUT requests repeatedly yields the exact same server state as a single invocation."
                        }
                    ]
                }
            }
        ]

        print("[*] Populating Courses, Curriculum & Assessments...")
        created_courses = []

        for c_data in courses_data:
            course = Course(
                title=c_data["title"],
                description=c_data["description"],
                category=c_data["category"],
                difficulty=c_data["difficulty"],
                duration=c_data["duration"],
                instructor=c_data["instructor"],
                thumbnail=c_data["thumbnail"],
                rating=c_data["rating"],
                learning_objectives=c_data["learning_objectives"],
                published=True,
                created_at=datetime.utcnow() - timedelta(days=20)
            )
            db.add(course)
            db.commit()
            db.refresh(course)
            created_courses.append(course)

            # Modules & Lessons
            for m_idx, m_data in enumerate(c_data["modules"], start=1):
                module = Module(
                    course_id=course.id,
                    title=m_data["title"],
                    description=m_data["description"],
                    order=m_idx
                )
                db.add(module)
                db.commit()
                db.refresh(module)

                for l_idx, l_data in enumerate(m_data["lessons"], start=1):
                    # Intelligent skill/topic assignment
                    topic_val = l_data.get("topic")
                    if not topic_val:
                        comb = (l_data["title"] + " " + m_data["title"]).lower()
                        if "variable" in comb or "primitive" in comb or "fundamental" in comb or "syntax" in comb or "operator" in comb:
                            topic_val = "Variables"
                        elif "loop" in comb or "iteration" in comb or "comprehension" in comb or "conditional" in comb or "branching" in comb:
                            topic_val = "Loops"
                        elif "function" in comb or "modular" in comb or "parameter" in comb:
                            topic_val = "Functions"
                        elif "class" in comb or "object" in comb or "oop" in comb or "inheritance" in comb or "polymorphism" in comb:
                            topic_val = "OOP"
                        elif "tree" in comb or "graph" in comb or "traversal" in comb:
                            topic_val = "Trees & Graphs"
                        elif "stack" in comb or "queue" in comb or "linked list" in comb or "array" in comb:
                            topic_val = "Data Structures"
                        elif "algorithm" in comb or "search" in comb or "sort" in comb or "complexity" in comb:
                            topic_val = "Algorithms"
                        elif "sql" in comb or "query" in comb or "database" in comb or "join" in comb or "normalization" in comb:
                            topic_val = "SQL & Modeling"
                        elif "api" in comb or "rest" in comb or "endpoint" in comb or "fastapi" in comb or "async" in comb:
                            topic_val = "REST APIs"
                        else:
                            topic_val = "General"

                    lesson = Lesson(
                        module_id=module.id,
                        title=l_data["title"],
                        content=l_data["content"],
                        video_url=l_data["video_url"] or None,
                        resource_url=l_data["resource_url"] or None,
                        duration=l_data["duration"],
                        topic=topic_val,
                        order=l_idx
                    )
                    db.add(lesson)

            db.commit()

            # Assessment & Questions
            asm_data = c_data["assessment"]
            asm_topic = asm_data.get("topic")
            if not asm_topic:
                comb_asm = (asm_data["title"] + " " + course.title).lower()
                if "python" in comb_asm:
                    asm_topic = "Variables & Loops"
                elif "data structure" in comb_asm or "algorithm" in comb_asm:
                    asm_topic = "Data Structures & Algorithms"
                elif "database" in comb_asm or "sql" in comb_asm:
                    asm_topic = "SQL & Relational Modeling"
                else:
                    asm_topic = "Web Architecture & APIs"

            assessment = Assessment(
                course_id=course.id,
                title=asm_data["title"],
                description=asm_data["description"],
                topic=asm_topic,
                pass_percentage=asm_data["pass_percentage"]
            )
            db.add(assessment)
            db.commit()
            db.refresh(assessment)

            for q_data in asm_data["questions"]:
                q = Question(
                    assessment_id=assessment.id,
                    question_text=q_data["question_text"],
                    option_a=q_data["option_a"],
                    option_b=q_data["option_b"],
                    option_c=q_data["option_c"],
                    option_d=q_data["option_d"],
                    correct_option=q_data["correct_option"],
                    explanation=q_data["explanation"]
                )
                db.add(q)

            db.commit()

        # 4. Enroll demo student and populate initial realistic progress
        print("[*] Enrolling Demo Student & generating realistic progress...")
        c_python = created_courses[0]
        c_dsa = created_courses[1]
        c_dbms = created_courses[2]

        # Enroll in Python course
        enr_python = Enrollment(
            user_id=student.id,
            course_id=c_python.id,
            enrolled_at=datetime.utcnow() - timedelta(days=12),
            progress=66.7
        )
        db.add(enr_python)

        # Mark Python lessons 1, 2, 3, 4 completed
        all_py_lessons = []
        for m in c_python.modules:
            for l in m.lessons:
                all_py_lessons.append(l)

        for i, l in enumerate(all_py_lessons[:4]):
            lp = LessonProgress(
                user_id=student.id,
                lesson_id=l.id,
                completed=True,
                completed_at=datetime.utcnow() - timedelta(days=10 - (i * 2))
            )
            db.add(lp)

        # Python assessment result
        py_asm = c_python.assessments[0]
        res_py = AssessmentResult(
            user_id=student.id,
            assessment_id=py_asm.id,
            score=4,
            total_questions=5,
            percentage=80.0,
            passed=True,
            answers_json=json.dumps({"1": "B", "2": "B", "3": "A", "4": "B", "5": "A"}),
            completed_at=datetime.utcnow() - timedelta(days=4)
        )
        db.add(res_py)

        # Enroll in DSA
        enr_dsa = Enrollment(
            user_id=student.id,
            course_id=c_dsa.id,
            enrolled_at=datetime.utcnow() - timedelta(days=8),
            progress=50.0
        )
        db.add(enr_dsa)
        for l in c_dsa.modules[0].lessons:
            lp = LessonProgress(
                user_id=student.id,
                lesson_id=l.id,
                completed=True,
                completed_at=datetime.utcnow() - timedelta(days=5)
            )
            db.add(lp)

        dsa_asm = c_dsa.assessments[0]
        res_dsa = AssessmentResult(
            user_id=student.id,
            assessment_id=dsa_asm.id,
            score=5,
            total_questions=5,
            percentage=100.0,
            passed=True,
            answers_json=json.dumps({"1": "B", "2": "B", "3": "B", "4": "A", "5": "B"}),
            completed_at=datetime.utcnow() - timedelta(days=2)
        )
        db.add(res_dsa)

        # Enroll extra students to populate admin analytics
        for idx, s in enumerate(extra_students):
            for c in created_courses[:3]:
                db.add(Enrollment(
                    user_id=s.id,
                    course_id=c.id,
                    enrolled_at=datetime.utcnow() - timedelta(days=15 - idx),
                    progress=float((idx + 1) * 25 % 100)
                ))
            # Assessment submission
            db.add(AssessmentResult(
                user_id=s.id,
                assessment_id=created_courses[0].assessments[0].id,
                score=4,
                total_questions=5,
                percentage=80.0,
                passed=True,
                completed_at=datetime.utcnow() - timedelta(days=3 + idx)
            ))

        db.commit()

        print("=" * 60)
        print("[+] DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Admin Account   : admin@elearning.com / admin123")
        print("Student Account : student@elearning.com / student123")
        print("Total Courses   :", len(created_courses))
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"[-] Error during database seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
