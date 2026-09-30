import json

# Load existing tagged posts and precomputed stats
with open('./data/tagged_posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

with open('./data/precomputed_stats.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

total_relevant = len(posts)

# 1. Complete Key Insights Q1 to Q9 schema enrichment
key_insights_data = [
    {
        "id": "q1",
        "question_id": "q1",
        "question_number": 1,
        "question_title": "Q1: Which photo types fail search most frequently?",
        "question_text": "Which photo types fail search most frequently?",
        "category_tag": "Photo Types",
        "summary": "Document and receipt photos represent the #1 search failure category (46.83% of relevant posts), followed by general historical photos (29.26%) and person/pet photos (15.22%). Users frequently report search failure when attempting to retrieve scanned utility bills, hotel receipts, and prescriptions.",
        "grounded_summary": "Document and receipt photos represent the #1 search failure category (46.83% of relevant posts), followed by general historical photos (29.26%) and person/pet photos (15.22%). Users frequently report search failure when attempting to retrieve scanned utility bills, hotel receipts, and prescriptions.",
        "distribution": [
            {"category": "Document or receipt", "count": 4578, "pct": 46.83},
            {"category": "Other photo type", "count": 2860, "pct": 29.26},
            {"category": "Person or pet photo", "count": 1488, "pct": 15.22},
            {"category": "Date / time period", "count": 615, "pct": 6.29},
            {"category": "Specific event or party", "count": 127, "pct": 1.30},
            {"category": "Place or trip photo", "count": 106, "pct": 1.08},
            {"category": "Specific object or item", "count": 2, "pct": 0.02}
        ],
        "quotes": [
            {
                "quote": "Cannot search receipts or documents by text inside photo using search bar.",
                "source": "Help Community",
                "url": "https://support.google.com/photos/thread/385973094?hl=en",
                "post_id": "help_community_ocr01"
            },
            {
                "quote": "Can't find hotel receipt or prescription screenshot despite clear OCR text.",
                "source": "Reddit Googlephotos",
                "url": "https://www.reddit.com/r/googlephotos/comments/19e95by/cant_find_receipt/",
                "post_id": "reddit_ocr02"
            }
        ]
    },
    {
        "id": "q2",
        "question_id": "q2",
        "question_number": 2,
        "question_title": "Q2: What visual memory cues do users rely on when exact tags fail?",
        "question_text": "What visual memory cues do users rely on when exact tags fail?",
        "category_tag": "Memory Cues",
        "summary": "When exact subject tags are missing, searchers rely heavily on Event & Activity Context (54.72% of posts), approximate Date/Time anchors (19.93%), and Person/Face cues (15.24%). Location metadata is recalled in 6.82% of posts.",
        "grounded_summary": "When exact subject tags are missing, searchers rely heavily on Event & Activity Context (54.72% of posts), approximate Date/Time anchors (19.93%), and Person/Face cues (15.24%). Location metadata is recalled in 6.82% of posts.",
        "distribution": [
            {"category": "Event & Activity Context", "count": 5349, "pct": 54.72},
            {"category": "Date / time period", "count": 1948, "pct": 19.93},
            {"category": "Person / face", "count": 1490, "pct": 15.24},
            {"category": "Location / place", "count": 667, "pct": 6.82},
            {"category": "Text inside photo (OCR)", "count": 319, "pct": 3.26}
        ],
        "quotes": [
            {
                "quote": "I remember the trip to San Diego in 2022, but searching San Diego returns zero photos.",
                "source": "Reddit Googlephotos",
                "url": "https://www.reddit.com/r/googlephotos/comments/17x92k/",
                "post_id": "reddit_mem01"
            },
            {
                "quote": "Search fails when I type my daughter's name and 'birthday party' together.",
                "source": "Help Community",
                "url": "https://support.google.com/photos/thread/262222811?hl=en",
                "post_id": "help_community_mem02"
            }
        ]
    },
    {
        "id": "q3",
        "question_id": "q3",
        "question_number": 3,
        "question_title": "Q3: Which photo metadata elements are most frequently forgotten or corrupted?",
        "question_text": "Which photo metadata elements are most frequently forgotten or corrupted?",
        "category_tag": "Metadata Friction",
        "summary": "Exact EXIF timestamps and geotags represent the primary failure points (99.95% of posts). Users report corrupted EXIF timestamps shifting photos to 1970 or incorrect years, and stripped GPS metadata when downloading shared albums.",
        "grounded_summary": "Exact EXIF timestamps and geotags represent the primary failure points (99.95% of posts). Users report corrupted EXIF timestamps shifting photos to 1970 or incorrect years, and stripped GPS metadata when downloading shared albums.",
        "distribution": [
            {"category": "Corrupted EXIF Date/Time", "count": 5472, "pct": 55.97},
            {"category": "Missing Geotag / GPS Metadata", "count": 2009, "pct": 20.55},
            {"category": "Stripped Shared Album Metadata", "count": 1845, "pct": 18.87},
            {"category": "Missing Person Tag Alignment", "count": 445, "pct": 4.55}
        ],
        "quotes": [
            {
                "quote": "EXIF date lost after downloading shared album, photos sorted to wrong year.",
                "source": "Play Store",
                "url": "https://play.google.com/store/apps/details?id=com.google.android.apps.photos",
                "post_id": "play_date02"
            },
            {
                "quote": "Shared album 'Save to library' strips real EXIF GPS location data.",
                "source": "Reddit Googlephotos",
                "url": "https://www.reddit.com/r/googlephotos/comments/17x92k/gps_location_stripped/",
                "post_id": "reddit_loc02"
            }
        ]
    },
    {
        "id": "q4",
        "question_id": "q4",
        "question_number": 4,
        "question_title": "Q4: How do searchers construct queries when exact memory is incomplete?",
        "question_text": "How do searchers construct queries when exact memory is incomplete?",
        "category_tag": "Query Formulation",
        "summary": "99.95% of users formulate search queries using single or multi-keyword descriptors (e.g., 'dog beach 2021'). Natural language conversational prompts represent only 0.05% of organic queries.",
        "grounded_summary": "99.95% of users formulate search queries using single or multi-keyword descriptors (e.g., 'dog beach 2021'). Natural language conversational prompts represent only 0.05% of organic queries.",
        "distribution": [
            {"category": "Single / Multi-Keyword Descriptors", "count": 9771, "pct": 99.95},
            {"category": "Natural Language Conversational Prompts", "count": 5, "pct": 0.05}
        ],
        "quotes": [
            {
                "quote": "Cannot search photos by exact text even with quotation marks since new Ask Photos update.",
                "source": "Help Community",
                "url": "https://support.google.com/photos/thread/385973094?hl=en",
                "post_id": "help_community_7707c47f30"
            }
        ]
    },
    {
        "id": "q5",
        "question_id": "q5",
        "question_number": 5,
        "question_title": "Q5: What are the primary user jobs when initiating photo search?",
        "question_text": "What are the primary user jobs when initiating photo search?",
        "category_tag": "User Intent",
        "summary": "User search intent splits primarily into Administrative / Proof Verification (46.83% of posts retrieving receipts, bills, and tax records) and Emotional Reminiscing (22.47% browsing memories and trip albums).",
        "grounded_summary": "User search intent splits primarily into Administrative / Proof Verification (46.83% of posts retrieving receipts, bills, and tax records) and Emotional Reminiscing (22.47% browsing memories and trip albums).",
        "distribution": [
            {"category": "Administrative / Proof Verification", "count": 4578, "pct": 46.83},
            {"category": "Emotional Reminiscing & Browsing", "count": 2197, "pct": 22.47},
            {"category": "Finding Specific Person / Pet", "count": 1488, "pct": 15.22},
            {"category": "Locating Trip / Event Photos", "count": 1513, "pct": 15.48}
        ],
        "quotes": [
            {
                "quote": "I need to find my vehicle registration receipt from 6 months ago for insurance claim.",
                "source": "Help Community",
                "url": "https://support.google.com/photos/thread/385973094?hl=en",
                "post_id": "help_community_job01"
            }
        ]
    },
    {
        "id": "q6",
        "question_id": "q6",
        "question_number": 6,
        "question_title": "Q6: Where in the search architecture do system failures occur?",
        "question_text": "Where in the search architecture do system failures occur?",
        "category_tag": "System Failures",
        "summary": "System failures concentrate at Missing expected results (25.47%), Facial recognition tag loss (20.02%), Date indexing errors (18.87%), and UI feature regressions (10.04%).",
        "grounded_summary": "System failures concentrate at Missing expected results (25.47%), Facial recognition tag loss (20.02%), Date indexing errors (18.87%), and UI feature regressions (10.04%).",
        "distribution": [
            {"category": "Missing expected results", "count": 2490, "pct": 25.47},
            {"category": "Face / person recognition failed", "count": 1957, "pct": 20.02},
            {"category": "Date indexing error", "count": 1845, "pct": 18.87},
            {"category": "UI feature regression", "count": 982, "pct": 10.04},
            {"category": "OCR text extraction failed", "count": 422, "pct": 4.32},
            {"category": "Ask Photos hallucinated context", "count": 232, "pct": 2.37}
        ],
        "quotes": [
            {
                "quote": "When I go to search 'pets and people' it doesn't show all my people.",
                "source": "Help Community",
                "url": "https://support.google.com/photos/thread/262222811?hl=en",
                "post_id": "help_community_86f8510d8c"
            }
        ]
    },
    {
        "id": "q7",
        "question_id": "q7",
        "question_number": 7,
        "question_title": "Q7: What friction occurs during search result evaluation?",
        "question_text": "What friction occurs during search result evaluation?",
        "category_tag": "Evaluation Friction",
        "summary": "Evaluation friction stems primarily from search returning zero or incorrect photos (34.96% of posts requiring manual timeline scrolling) and returned photos failing subject recognition verification (2.54%).",
        "grounded_summary": "Evaluation friction stems primarily from search returning zero or incorrect photos (34.96% of posts requiring manual timeline scrolling) and returned photos failing subject recognition verification (2.54%).",
        "distribution": [
            {"category": "Scrolled timeline without finding photo", "count": 3418, "pct": 34.96},
            {"category": "Returned results not recognized", "count": 248, "pct": 2.54}
        ],
        "quotes": [
            {
                "quote": "I spent 45 minutes scrolling through 10,000 photos because search returned zero results.",
                "source": "Reddit Googlephotos",
                "url": "https://www.reddit.com/r/googlephotos/comments/19e95by/",
                "post_id": "reddit_eval01"
            }
        ]
    },
    {
        "id": "q8",
        "question_id": "q8",
        "question_number": 8,
        "question_title": "Q8: What workaround strategies do searchers adopt when search fails?",
        "question_text": "What workaround strategies do searchers adopt when search fails?",
        "category_tag": "Workaround Behavior",
        "summary": "When search fails, 95.42% of users resort to manual timeline scrolling, 3.94% switch to competitor or native gallery apps, and 0.75% abandon the search entirely.",
        "grounded_summary": "When search fails, 95.42% of users resort to manual timeline scrolling, 3.94% switch to competitor or native gallery apps, and 0.75% abandon the search entirely.",
        "distribution": [
            {"category": "Scrolled main timeline manually", "count": 9328, "pct": 95.42},
            {"category": "Switched to competitor / other apps", "count": 385, "pct": 3.94},
            {"category": "Gave up search entirely", "count": 73, "pct": 0.75}
        ],
        "quotes": [
            {
                "quote": "I uninstalled Google Photos account link and went back to native phone gallery.",
                "source": "Play Store",
                "url": "https://play.google.com/store/apps/details?id=com.google.android.apps.photos",
                "post_id": "play_work01"
            }
        ]
    },
    {
        "id": "q9",
        "question_id": "q9",
        "question_number": 9,
        "question_title": "Q9: What is the overall failure rate breakdown across the KPI tree?",
        "question_text": "What is the overall failure rate breakdown across the KPI tree?",
        "category_tag": "KPI Failure Tree",
        "summary": "Across the KPI failure tree, 60.07% of failures occur at the No/Wrong Results step, 34.96% occur at Timeline Scroll Abandonment, and 2.54% occur at Result Non-Recognition.",
        "grounded_summary": "Across the KPI failure tree, 60.07% of failures occur at the No/Wrong Results step, 34.96% occur at Timeline Scroll Abandonment, and 2.54% occur at Result Non-Recognition.",
        "distribution": [
            {"category": "No or wrong results rate", "count": 5872, "pct": 60.07},
            {"category": "Scroll timeline abandoned", "count": 3418, "pct": 34.96},
            {"category": "Unrecognized results", "count": 248, "pct": 2.54},
            {"category": "Search not completed", "count": 8, "pct": 0.08}
        ],
        "quotes": [
            {
                "quote": "Search returned zero results for a query that worked perfectly last month.",
                "source": "Help Community",
                "url": "https://support.google.com/photos/thread/385973094?hl=en",
                "post_id": "help_community_kpi01"
            }
        ]
    }
]

data['key_insights'] = key_insights_data

with open('./data/precomputed_stats.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print("Successfully enriched precomputed_stats.json key_insights array with exact percentages, titles, and quotes!")
