"""Configurable starter content for JOMO quests, missions and achievements."""

CATEGORIES = {
    "movement_outdoors": "Movement & Outdoors",
    "social_connections": "Social Connections",
    "creativity_hobbies": "Creativity & Hobbies",
    "mindfulness_growth": "Mindfulness & Personal Growth",
    "learning_skills": "Learning & Skills",
    "digital_wellbeing": "Digital Wellbeing",
    "community_kindness": "Community & Kindness",
}

# code, title, category, minutes, difficulty, instructions
QUESTS = [
    ("Q001", "Morning Walk", "movement_outdoors", 15, "easy", "Walk outdoors for at least 15 minutes without recreational scrolling."),
    ("Q002", "Explore Somewhere New", "movement_outdoors", 25, "medium", "Visit a new public place and notice three interesting things."),
    ("Q003", "Nature Explorer", "movement_outdoors", 20, "medium", "Spend 20 minutes in a green space and observe five things."),
    ("Q004", "Move Your Body", "movement_outdoors", 20, "medium", "Complete 20 minutes of accessible physical activity."),
    ("Q005", "Weekend Adventure", "movement_outdoors", 45, "hard", "Complete a safe outdoor activity outside your normal routine."),
    ("Q006", "Catch Up With Someone", "social_connections", 15, "easy", "Have a meaningful, present conversation with someone you care about."),
    ("Q007", "Phone-Free Hangout", "social_connections", 30, "medium", "Spend 30 minutes with another person with recreational phone use put aside."),
    ("Q008", "Meet Someone New", "social_connections", 20, "hard", "Introduce yourself in a suitable social setting; choose a safe alternative if needed."),
    ("Q009", "Family Time", "social_connections", 30, "medium", "Complete an activity with family or chosen family."),
    ("Q010", "Spread Kindness", "social_connections", 15, "easy", "Perform one thoughtful act without expecting anything in return."),
    ("Q011", "Create Something", "creativity_hobbies", 20, "medium", "Draw, paint, build, craft or create something tangible."),
    ("Q012", "Try a New Hobby", "creativity_hobbies", 30, "medium", "Try an unfamiliar hobby for at least 30 minutes."),
    ("Q013", "Capture the Moment", "creativity_hobbies", 15, "easy", "Photograph three real-world details; uploading is not required."),
    ("Q014", "Make Something by Hand", "creativity_hobbies", 30, "medium", "Complete a simple physical craft or DIY project."),
    ("Q015", "Music Without Scrolling", "creativity_hobbies", 20, "easy", "Practise, sing or listen to music without recreational scrolling."),
    ("Q016", "Mindful Moment", "mindfulness_growth", 10, "easy", "Spend 10 minutes meditating, breathing or sitting quietly."),
    ("Q017", "Journal Your Thoughts", "mindfulness_growth", 10, "easy", "Write three things you experienced, appreciated or learned."),
    ("Q018", "Read Outside", "mindfulness_growth", 20, "medium", "Read a physical book or printed material outdoors for 20 minutes."),
    ("Q019", "Gratitude Challenge", "mindfulness_growth", 5, "easy", "Write three things you are grateful for."),
    ("Q020", "Step Outside Your Comfort Zone", "mindfulness_growth", 30, "hard", "Complete a safe, personally selected activity that gently challenges you."),
    ("Q021", "Learn Something New", "learning_skills", 20, "medium", "Learn about a new subject using an educational resource."),
    ("Q022", "Master a New Skill", "learning_skills", 30, "medium", "Practise a chosen skill for at least 30 minutes."),
    ("Q023", "Read and Discover", "learning_skills", 20, "medium", "Read an educational resource and record one thing learned."),
    ("Q024", "Teach Someone Something", "learning_skills", 15, "medium", "Teach someone a concept or skill you understand."),
    ("Q025", "Build Something", "learning_skills", 45, "hard", "Complete a small practical project."),
    ("Q026", "Social Media Break", "digital_wellbeing", 30, "easy", "Avoid recreational social media for 30 minutes."),
    ("Q027", "One Hour Offline", "digital_wellbeing", 60, "hard", "Spend one hour away from recreational screen use."),
    ("Q028", "Phone-Free Mealtime", "digital_wellbeing", 20, "easy", "Complete one meal without entertainment feeds."),
    ("Q029", "No-Scroll Morning", "digital_wellbeing", 30, "medium", "Avoid recreational social media for the first 30 minutes after waking."),
    ("Q030", "Evening Wind Down", "digital_wellbeing", 30, "medium", "Avoid recreational scrolling during the final 30 minutes before sleep."),
    ("Q031", "Help Someone Out", "community_kindness", 20, "easy", "Offer safe, practical help to someone who could use it."),
    ("Q032", "Clean Your Space", "community_kindness", 15, "easy", "Organise or clean your room, desk or personal space."),
    ("Q033", "Community Explorer", "community_kindness", 20, "medium", "Discover a local community event or volunteer opportunity."),
    ("Q034", "Give Back", "community_kindness", 45, "hard", "Complete a safe and appropriate volunteering or community activity."),
    ("Q035", "Share a Positive Moment", "community_kindness", 5, "easy", "Express genuine appreciation to someone."),
]

XP_BY_DIFFICULTY = {"easy": 20, "medium": 40, "hard": 70}

# code, title, type, metric, target, categories, XP reward
MISSIONS = [
    ("DM001", "Complete any quest", "daily", "quest_count", 1, None, 15),
    ("DM002", "Earn 30 quest XP", "daily", "xp_earned", 30, None, 15),
    ("DM003", "Take a digital wellbeing break", "daily", "category_count", 1, ["digital_wellbeing"], 15),
    ("DM004", "Complete an outdoor activity", "daily", "category_count", 1, ["movement_outdoors"], 15),
    ("DM005", "Complete a mindfulness activity", "daily", "category_count", 1, ["mindfulness_growth"], 15),
    ("DM006", "Have an offline interaction", "daily", "category_count", 1, ["social_connections"], 15),
    ("DM007", "Complete a creativity activity", "daily", "category_count", 1, ["creativity_hobbies"], 15),
    ("DM008", "Read or learn something", "daily", "category_count", 1, ["learning_skills"], 15),
    ("DM009", "Complete two quests", "daily", "quest_count", 2, None, 25),
    ("DM010", "Spend 45 meaningful minutes offline", "daily", "minutes", 45, None, 20),
    ("WM001", "The Explorer", "weekly", "quest_count", 5, None, 100),
    ("WM002", "Outside More", "weekly", "category_count", 3, ["movement_outdoors"], 80),
    ("WM003", "Social Butterfly", "weekly", "category_count", 3, ["social_connections"], 80),
    ("WM004", "Digital Detox", "weekly", "category_count", 3, ["digital_wellbeing"], 100),
    ("WM005", "The Creator", "weekly", "category_count", 3, ["creativity_hobbies", "learning_skills"], 80),
    ("WM006", "Community Champion", "weekly", "category_count", 2, ["community_kindness"], 80),
    ("WM007", "The Balanced Week", "weekly", "distinct_categories", 3, None, 100),
    ("WM008", "Consistency Challenge", "weekly", "distinct_days", 4, None, 100),
]

# code, name, metric, target, category, XP reward
ACHIEVEMENTS = [
    ("A001", "First Steps", "quest_count", 1, None, 20),
    ("A002", "Getting Started", "quest_count", 5, None, 40),
    ("A003", "Explorer", "quest_count", 25, None, 100),
    ("A004", "Quest Master", "quest_count", 50, None, 150),
    ("A005", "Offline Champion", "quest_count", 100, None, 300),
    ("A006", "Nature Lover", "category_count", 10, "movement_outdoors", 75),
    ("A007", "People Person", "category_count", 10, "social_connections", 75),
    ("A008", "Creative Mind", "category_count", 10, "creativity_hobbies", 75),
    ("A009", "Curious Mind", "category_count", 10, "learning_skills", 75),
    ("A010", "Digital Balance", "category_count", 10, "digital_wellbeing", 75),
]
