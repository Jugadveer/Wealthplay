"""
Load course content from course_modules folder structure
"""
import json
import os
from pathlib import Path
from django.conf import settings

# Course folder mapping
COURSE_FOLDER_MAP = {
    "money-basics": {"title": "Money Basics", "level": "Beginner"},
    "budgeting": {"title": "Budgeting & Saving", "level": "Beginner"},
    "banking-products": {"title": "Banking Products", "level": "Beginner"},
    "investing-basics": {"title": "Investing Basics", "level": "Beginner"},
    "stock-market-101": {"title": "Stock Market 101", "level": "Beginner"},
    "mutual-funds-sips": {"title": "Mutual Funds & SIPs", "level": "Beginner"},
    "emergency-insurance": {"title": "Emergency Fund & Insurance", "level": "Beginner"},
    "financial-goals": {"title": "Financial Goals", "level": "Beginner"},
    "scams-safety": {"title": "Scams & Safety", "level": "Beginner"},
    "debt-credit": {"title": "Debt & Credit", "level": "Intermediate"},
    "stocks-etfs": {"title": "Stocks & ETFs", "level": "Intermediate"},
    "tax-planning": {"title": "Tax Planning", "level": "Intermediate"},
    "retirement": {"title": "Retirement Planning", "level": "Intermediate"},
    "portfolio-building": {"title": "Portfolio Building", "level": "Intermediate"},
    "behavioral-finance": {"title": "Money Psychology", "level": "Intermediate"},
    "market-fundamentals": {"title": "Market Fundamentals", "level": "Intermediate"},
    "risk-management": {"title": "Risk Management", "level": "Intermediate"},
    "real-estate": {"title": "Real Estate Basics", "level": "Advanced"},
    "crypto-alternatives": {"title": "Crypto & Alternatives", "level": "Advanced"},
    "investing-101": {"title": "Investing 101", "level": "Beginner"},
}

BASE_DIR = Path(settings.BASE_DIR)
COURSE_MODULES_DIR = BASE_DIR / 'course_modules'


def load_courses_from_folders():
    """Load all courses from course_modules folder structure"""
    courses = []
    
    if not COURSE_MODULES_DIR.exists():
        print(f"Course modules directory not found: {COURSE_MODULES_DIR}")
        return courses
    
    for course_folder in sorted(COURSE_MODULES_DIR.iterdir()):
        if not course_folder.is_dir():
            continue
        
        course_id = course_folder.name
        course_info = COURSE_FOLDER_MAP.get(course_id, {
            "title": course_id.replace('-', ' ').title(),
            "level": "Beginner"
        })
        
        modules = []
        module_order = 1
        
        # Load all modules in this course
        for module_folder in sorted(course_folder.iterdir()):
            if not module_folder.is_dir():
                continue
            
            module_id = module_folder.name
            
            # Load module content files
            flash_cards_file = module_folder / 'flash_cards.json'
            mcqs_file = module_folder / 'mcqs.json'
            qna_file = module_folder / 'qna.json'
            
            # Read flash cards
            flash_cards = []
            if flash_cards_file.exists():
                try:
                    with open(flash_cards_file, 'r', encoding='utf-8') as f:
                        flash_cards = json.load(f)
                except Exception as e:
                    print(f"Error reading flash_cards.json for {course_id}/{module_id}: {e}")
            
            # Read MCQs
            mcqs = []
            if mcqs_file.exists():
                try:
                    with open(mcqs_file, 'r', encoding='utf-8') as f:
                        mcqs = json.load(f)
                except Exception as e:
                    print(f"Error reading mcqs.json for {course_id}/{module_id}: {e}")
            
            # Read Q&A
            qna = []
            if qna_file.exists():
                try:
                    with open(qna_file, 'r', encoding='utf-8') as f:
                        qna = json.load(f)
                        # Transform to expected format
                        if qna and isinstance(qna[0], dict):
                            if 'question' in qna[0] and 'answer' in qna[0]:
                                qna = [{"q": item.get('question'), "a": item.get('answer'), "explanation": item.get('explanation', '')} for item in qna]
                except Exception as e:
                    print(f"Error reading qna.json for {course_id}/{module_id}: {e}")
            
            # Extract title from first flash card or use module_id
            # Also check if there's a metadata file or use folder name
            module_title = module_id.upper().replace('-', ' ').replace('_', ' ')
            if flash_cards and len(flash_cards) > 0:
                first_card = flash_cards[0]
                module_title = first_card.get('theory_title') or first_card.get('topic') or module_title
            
            # Build module object
            module = {
                'id': module_id,
                'title': module_title,
                'summary': qna[0].get('a', '')[:200] if qna else '',
                'order': module_order,
                'flash_cards': flash_cards,
                'mcqs': mcqs,
                'fixed_qna': qna,
                'xp_reward': 50 + (module_order * 25),  # Default XP reward
            }
            
            modules.append(module)
            module_order += 1
        
        # Build course object
        # Normalize level to lowercase for consistency
        course_level = course_info['level'].lower() if course_info.get('level') else 'beginner'
        course = {
            'id': course_id,
            'title': course_info['title'],
            'level': course_level,
            'xp_to_unlock': 0 if course_level == 'beginner' else (750 if course_level == 'intermediate' else 1200),
            'modules': modules,
            'source': 'course_modules'
        }
        
        courses.append(course)
    
    return courses


def get_module_from_folder(course_id, module_id):
    """Get a specific module from course_modules folder"""
    module_path = COURSE_MODULES_DIR / course_id / module_id
    
    if not module_path.exists():
        return None
    
    # Load all module files
    flash_cards = []
    mcqs = []
    qna = []
    
    flash_cards_file = module_path / 'flash_cards.json'
    if flash_cards_file.exists():
        try:
            with open(flash_cards_file, 'r', encoding='utf-8') as f:
                flash_cards = json.load(f)
        except Exception as e:
            print(f"Error reading flash_cards.json: {e}")
    
    mcqs_file = module_path / 'mcqs.json'
    if mcqs_file.exists():
        try:
            with open(mcqs_file, 'r', encoding='utf-8') as f:
                mcqs = json.load(f)
        except Exception as e:
            print(f"Error reading mcqs.json: {e}")
    
    qna_file = module_path / 'qna.json'
    if qna_file.exists():
        try:
            with open(qna_file, 'r', encoding='utf-8') as f:
                qna_data = json.load(f)
                # Transform to expected format
                if qna_data and isinstance(qna_data[0], dict):
                    if 'question' in qna_data[0] and 'answer' in qna_data[0]:
                        qna = [{"q": item.get('question'), "a": item.get('answer'), "explanation": item.get('explanation', '')} for item in qna_data]
                    else:
                        qna = qna_data
        except Exception as e:
            print(f"Error reading qna.json: {e}")
    
    # Extract module title
    module_title = module_id.upper().replace('-', ' ').replace('_', ' ')
    if flash_cards and len(flash_cards) > 0:
        first_card = flash_cards[0]
        module_title = first_card.get('theory_title') or first_card.get('topic') or module_title
    
    # Get theory text from first flash card
    theory_text = ''
    if flash_cards and len(flash_cards) > 0:
        theory_text = flash_cards[0].get('theory_content', '')
    
    course_info = COURSE_FOLDER_MAP.get(course_id, {"title": course_id.replace('-', ' ').title(), "level": "Beginner"})
    
    return {
        'id': module_id,
        'title': module_title,
        'summary': qna[0].get('a', '')[:200] if qna else '',
        'theory_text': theory_text,
        'flash_cards': flash_cards,
        'mcqs': mcqs,
        'fixed_qna': qna,
        'xp_reward': 50,
    }, {
        'id': course_id,
        'title': course_info['title'],
        'level': course_info['level'],
    }

