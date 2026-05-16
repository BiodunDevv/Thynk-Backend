from app.core.constants import PromptCategory
from app.models.prompt_template import PromptTemplate

TEMPLATES = [
    # ── DESIGN ──────────────────────────────────────────────────────────────
    {
        "title": "Mobile-First Landing Page UX Brief",
        "description": "Generates a detailed UX brief for a mobile-first product landing page — including goals, audience personas, hierarchy, conversion points, and interaction patterns.",
        "category": PromptCategory.DESIGN,
        "template_content": (
            "You are a senior UX designer. Write a comprehensive UX brief for a mobile-first landing page for the following product:\n\n"
            "[PRODUCT DESCRIPTION]\n\n"
            "The brief must cover:\n"
            "1. Business goals and success metrics\n"
            "2. Primary and secondary user personas (include pain points, motivations, and device context)\n"
            "3. Information hierarchy — what the user sees in each scroll section\n"
            "4. Conversion points and micro-interactions (CTAs, trust signals, social proof placement)\n"
            "5. Accessibility considerations (contrast ratios, touch targets, screen-reader notes)\n"
            "6. Component inventory (hero, feature grid, testimonials, pricing, footer)\n"
            "7. Performance and PWA requirements\n\n"
            "Tone: Professional, precise, actionable. Output in structured sections with headers."
        ),
        "tags": ["ux", "design", "landing-page", "mobile", "brief"],
        "is_premium": False,
    },
    {
        "title": "Design System Component Spec",
        "description": "Creates a detailed component specification document for a design system — covering variants, states, tokens, accessibility, and usage guidelines.",
        "category": PromptCategory.DESIGN,
        "template_content": (
            "You are a design system architect. Write a full component specification for the following UI component:\n\n"
            "[COMPONENT NAME, e.g. Button, Modal, Data Table]\n\n"
            "For the component [BRAND/PRODUCT], produce:\n\n"
            "1. Component overview and intended use cases\n"
            "2. Visual variants (primary, secondary, ghost, destructive, etc.) with exact design token references\n"
            "3. Interactive states: default, hover, focus, active, loading, disabled, error\n"
            "4. Size and spacing scales (sm / md / lg)\n"
            "5. Composition rules — what can and cannot be nested inside\n"
            "6. Accessibility requirements (ARIA roles, keyboard nav, focus management)\n"
            "7. Do's and Don'ts with brief rationale for each\n"
            "8. Related components and when to use them instead\n\n"
            "Format: Structured spec document, table format where applicable."
        ),
        "tags": ["design-system", "component", "spec", "tokens", "accessibility"],
        "is_premium": True,
    },

    # ── DEVELOPMENT ──────────────────────────────────────────────────────────
    {
        "title": "REST API Integration Task",
        "description": "Produces a structured technical prompt for implementing a backend API integration — including endpoint contract, edge cases, error handling, and rollout notes.",
        "category": PromptCategory.DEVELOPMENT,
        "template_content": (
            "You are a senior backend engineer. Write a complete technical specification for integrating the following external API:\n\n"
            "Service: [SERVICE NAME]\n"
            "Integration goal: [WHAT WE ARE BUILDING]\n"
            "Tech stack: [LANGUAGE / FRAMEWORK]\n\n"
            "Produce:\n"
            "1. Endpoint contract — method, URL, request/response schemas with types\n"
            "2. Authentication mechanism and token lifecycle\n"
            "3. Rate-limit handling and backoff strategy\n"
            "4. Error codes and what the application should do for each\n"
            "5. Idempotency requirements (especially for POST/PATCH)\n"
            "6. Webhook configuration (if applicable) with signature verification\n"
            "7. Unit and integration test checklist\n"
            "8. Staging vs production environment differences\n"
            "9. Rollout notes: feature flag, monitoring metric to watch, rollback plan\n\n"
            "Be specific and opinionated. Avoid generic filler."
        ),
        "tags": ["backend", "api", "integration", "development", "spec"],
        "is_premium": False,
    },
    {
        "title": "Code Review Checklist Prompt",
        "description": "Generates a thorough, role-aware code review prompt for any pull request — covering correctness, security, performance, and maintainability.",
        "category": PromptCategory.DEVELOPMENT,
        "template_content": (
            "You are a staff engineer conducting a thorough code review. Review the following pull request:\n\n"
            "PR Title: [PR TITLE]\n"
            "Language/Framework: [LANGUAGE / FRAMEWORK]\n"
            "Context: [BRIEF DESCRIPTION OF WHAT THIS PR DOES]\n\n"
            "Diff:\n"
            "```\n[PASTE DIFF HERE]\n```\n\n"
            "Evaluate across these dimensions and provide specific, line-referenced feedback:\n\n"
            "1. Correctness — logic errors, off-by-one, race conditions, null/undefined handling\n"
            "2. Security — injection risks, exposed secrets, auth bypass, IDOR, input validation\n"
            "3. Performance — N+1 queries, unnecessary re-renders, blocking calls, memory leaks\n"
            "4. Maintainability — naming clarity, function length, single responsibility, test coverage\n"
            "5. API contract — breaking changes, versioning impact\n"
            "6. Edge cases not handled\n"
            "7. Suggested improvements with code snippets where helpful\n\n"
            "End with: LGTM / Request Changes / Blocking — with a 1-sentence justification."
        ),
        "tags": ["code-review", "development", "quality", "security"],
        "is_premium": False,
    },
    {
        "title": "Database Schema Design Review",
        "description": "Deep-reviews a proposed database schema — covering normalisation, indexing strategy, query patterns, and scalability concerns.",
        "category": PromptCategory.DEVELOPMENT,
        "template_content": (
            "You are a principal database engineer. Review the following schema and provide a detailed architectural assessment.\n\n"
            "Database type: [PostgreSQL / MongoDB / MySQL / etc.]\n"
            "Application type: [e.g. SaaS, e-commerce, analytics]\n\n"
            "Schema:\n"
            "```\n[PASTE SCHEMA / MODELS HERE]\n```\n\n"
            "Assess:\n"
            "1. Normalisation level and whether it is appropriate for the use case\n"
            "2. Index strategy — missing indexes, redundant indexes, composite index opportunities\n"
            "3. Query pattern fit — does the schema support the expected read/write patterns?\n"
            "4. Scalability ceiling — where will this break at 10x, 100x data volume?\n"
            "5. Data integrity — constraints, cascades, soft-delete patterns\n"
            "6. Naming conventions and consistency\n"
            "7. Migration risk — what is hard to change later and why\n"
            "8. Recommended schema changes with before/after SQL or model code\n\n"
            "Be blunt. Prioritise changes by impact."
        ),
        "tags": ["database", "schema", "development", "architecture", "performance"],
        "is_premium": True,
    },

    # ── CONTENT ─────────────────────────────────────────────────────────────
    {
        "title": "Long-Form Blog Post",
        "description": "Produces a structured, SEO-aware long-form blog post with a compelling angle, clear sections, and a strong call-to-action.",
        "category": PromptCategory.CONTENT,
        "template_content": (
            "Write a long-form blog post (1,500–2,000 words) on the following topic:\n\n"
            "Topic: [TOPIC]\n"
            "Target audience: [AUDIENCE]\n"
            "Primary keyword: [KEYWORD]\n"
            "Desired tone: [e.g. authoritative, conversational, inspiring]\n"
            "Publication: [BLOG / BRAND NAME]\n\n"
            "Structure:\n"
            "- Headline (magnetic, includes keyword naturally)\n"
            "- Meta description (155 chars max, includes keyword)\n"
            "- Opening hook — start with a surprising stat, counter-intuitive claim, or vivid scenario\n"
            "- 4–6 H2 sections, each with a sub-point or two\n"
            "- Pull quotes / callouts for shareability\n"
            "- Closing synthesis — what the reader should take away and do next\n"
            "- CTA (soft — link to related resource or newsletter)\n\n"
            "Guidelines: No generic filler, no lists of five that could be three, no passive voice where active works."
        ),
        "tags": ["blog", "content", "seo", "writing", "long-form"],
        "is_premium": False,
    },
    {
        "title": "YouTube Video Script",
        "description": "Writes a full YouTube video script with hook, structured chapters, B-roll notes, and an end screen CTA optimised for retention.",
        "category": PromptCategory.CONTENT,
        "template_content": (
            "Write a complete YouTube video script for the following:\n\n"
            "Topic: [TOPIC]\n"
            "Channel niche: [NICHE]\n"
            "Target audience: [AUDIENCE]\n"
            "Desired length: [e.g. 8–12 minutes]\n"
            "Tone: [e.g. educational, entertaining, documentary-style]\n\n"
            "Script format:\n"
            "[HOOK — first 30 seconds: open with a bold claim, question, or visual that makes viewers stay]\n"
            "[PATTERN INTERRUPT — 45 seconds in: change of pace or unexpected turn]\n"
            "[CHAPTER 1] — Title + narration + [B-ROLL NOTE]\n"
            "[CHAPTER 2] — ...\n"
            "[CHAPTER 3] — ...\n"
            "[RECAP + PAYOFF — deliver on the promise made in the hook]\n"
            "[CTA — subscribe, related video, comment prompt]\n\n"
            "Mark B-roll suggestions in [brackets]. Keep narration punchy — no sentence over 20 words if it can be two. Write for speech, not reading."
        ),
        "tags": ["youtube", "video", "script", "content", "creator"],
        "is_premium": False,
    },

    # ── MARKETING ────────────────────────────────────────────────────────────
    {
        "title": "Product Launch Email Sequence",
        "description": "Writes a 5-email launch sequence — from teaser to cart-close — with subject lines, preview text, and conversion-focused body copy.",
        "category": PromptCategory.MARKETING,
        "template_content": (
            "You are a direct-response email copywriter. Write a 5-email product launch sequence for:\n\n"
            "Product: [PRODUCT NAME AND DESCRIPTION]\n"
            "Audience: [TARGET AUDIENCE]\n"
            "Launch window: [e.g. 7 days]\n"
            "Offer/CTA: [DISCOUNT / BONUS / DEADLINE]\n"
            "Brand voice: [e.g. bold and punchy / warm and educational]\n\n"
            "For each email provide:\n"
            "- Email number and send timing (e.g. Day 1, Day 3)\n"
            "- Subject line (A/B variant if possible)\n"
            "- Preview text (90 chars max)\n"
            "- Full email body (include CTA button copy)\n"
            "- P.S. line (often the second most-read element)\n\n"
            "Email sequence arc:\n"
            "1. The problem/opportunity (no pitch)\n"
            "2. The solution reveal\n"
            "3. Social proof + objection handling\n"
            "4. Urgency / last chance reminder\n"
            "5. Final hours — cart close\n\n"
            "No clichés, no 'I hope this email finds you well.' Every line must earn its place."
        ),
        "tags": ["email", "marketing", "launch", "copywriting", "sequence"],
        "is_premium": True,
    },
    {
        "title": "Paid Ad Copy — Meta / Google",
        "description": "Produces a complete set of ad variations for Meta or Google Ads — headlines, primary text, descriptions, and hooks for different audience segments.",
        "category": PromptCategory.MARKETING,
        "template_content": (
            "You are a performance marketing specialist. Write a complete ad copy set for the following campaign:\n\n"
            "Product/Service: [PRODUCT]\n"
            "Platform: [Meta Ads / Google Ads / both]\n"
            "Target audience: [DEMOGRAPHICS + INTERESTS]\n"
            "Campaign goal: [Awareness / Leads / Sales]\n"
            "Key differentiator: [WHAT MAKES THIS UNIQUE]\n"
            "Offer: [DISCOUNT / FREE TRIAL / GUARANTEE]\n\n"
            "Deliverables:\n"
            "META ADS:\n"
            "- 3 × Primary text variations (100–125 words each, different emotional angles)\n"
            "- 5 × Headlines (40 chars max)\n"
            "- 3 × Descriptions (30 chars max)\n"
            "- 2 × Hook-first short-form video script intros (first 3 seconds)\n\n"
            "GOOGLE ADS (if applicable):\n"
            "- 15 × Responsive search ad headlines (30 chars max)\n"
            "- 4 × Descriptions (90 chars max)\n\n"
            "Label each variation by emotional angle: Fear of Missing Out / Social Proof / Curiosity / Direct Benefit."
        ),
        "tags": ["ads", "marketing", "meta", "google", "copywriting", "paid"],
        "is_premium": True,
    },

    # ── WRITING ──────────────────────────────────────────────────────────────
    {
        "title": "Short Story Opening Chapter",
        "description": "Generates a compelling opening chapter for a short story — establishing voice, world, character, and a hook that demands the next page.",
        "category": PromptCategory.WRITING,
        "template_content": (
            "Write the opening chapter (~1,000 words) of a short story with the following parameters:\n\n"
            "Genre: [GENRE]\n"
            "Setting: [TIME AND PLACE]\n"
            "Protagonist: [NAME, AGE, ONE-LINE ESSENCE]\n"
            "Central tension: [WHAT PROBLEM OR CONFLICT DRIVES THIS STORY]\n"
            "Tone/voice: [e.g. lyrical, terse, dark, wry]\n"
            "POV: [First / Third limited / Third omniscient]\n\n"
            "Requirements:\n"
            "- Open in media res — drop the reader into action or a moment that matters\n"
            "- Establish the protagonist's voice within the first 3 sentences\n"
            "- Ground the setting sensory-first — what the character sees, hears, smells\n"
            "- Plant one mystery or unanswered question by paragraph 3\n"
            "- End the chapter on a micro-cliffhanger or revelatory moment\n"
            "- Zero backstory dumps — reveal world and history through action and dialogue only\n\n"
            "Do not summarise what the story is about. Write the story."
        ),
        "tags": ["fiction", "writing", "short-story", "creative", "narrative"],
        "is_premium": False,
    },
    {
        "title": "Professional Bio (LinkedIn / Speaking)",
        "description": "Writes a polished first- and third-person professional bio optimised for LinkedIn, a conference programme, or a personal website About page.",
        "category": PromptCategory.WRITING,
        "template_content": (
            "Write professional bios in both first and third person for the following individual:\n\n"
            "Name: [NAME]\n"
            "Current role and company: [ROLE AT COMPANY]\n"
            "Years of experience: [YEARS] in [INDUSTRY/FIELD]\n"
            "Key achievements (3 bullet points): [ACHIEVEMENT 1], [ACHIEVEMENT 2], [ACHIEVEMENT 3]\n"
            "What they are known for: [UNIQUE ANGLE OR SPECIALITY]\n"
            "Personal touch (optional): [HOBBY / CAUSE / LOCATION]\n"
            "CTA: [WHAT THEY WANT READERS TO DO — connect / speak / hire / follow]\n\n"
            "Produce:\n"
            "1. SHORT BIO — 50 words, third person, for conference badges and panels\n"
            "2. MEDIUM BIO — 150 words, third person, for event programmes and press kits\n"
            "3. LONG BIO — 300 words, first person, for LinkedIn About and personal site\n\n"
            "Tone: Confident without being boastful. Specific over generic. Avoid buzzwords like 'passionate', 'results-driven', 'synergy'."
        ),
        "tags": ["bio", "writing", "linkedin", "personal-brand", "professional"],
        "is_premium": False,
    },

    # ── STUDENT ──────────────────────────────────────────────────────────────
    {
        "title": "University Essay Outline + Draft",
        "description": "Creates a structured essay outline and a full first draft for a given academic question — properly argued, cited, and formatted to university standards.",
        "category": PromptCategory.STUDENT,
        "template_content": (
            "You are an academic writing tutor. Help me write a university-level essay on the following:\n\n"
            "Essay question: [FULL QUESTION]\n"
            "Subject / discipline: [SUBJECT]\n"
            "Word count required: [WORD COUNT]\n"
            "Academic level: [Undergraduate Year 1 / Year 2 / Year 3 / Postgraduate]\n"
            "Citation style: [Harvard / APA / MLA / Chicago]\n"
            "Key sources to include (optional): [SOURCE 1], [SOURCE 2]\n\n"
            "Produce:\n"
            "PART 1 — OUTLINE\n"
            "- Thesis statement (1 sentence)\n"
            "- Introduction approach\n"
            "- 3–4 body paragraph topics with supporting argument and evidence direction\n"
            "- Counterargument paragraph\n"
            "- Conclusion angle\n\n"
            "PART 2 — FULL DRAFT\n"
            "Write the complete essay to the required word count. Use formal academic tone. Every claim must be supported. Flag where citations are needed with [CITE: author, year]. No padding — every paragraph must advance the argument."
        ),
        "tags": ["essay", "academic", "student", "university", "writing"],
        "is_premium": False,
    },
    {
        "title": "Exam Revision Study Guide",
        "description": "Produces a comprehensive, exam-focused revision guide for any topic — with key concepts, worked examples, memory aids, and predicted exam questions.",
        "category": PromptCategory.STUDENT,
        "template_content": (
            "You are an expert tutor. Create a complete revision guide for the following:\n\n"
            "Subject: [SUBJECT]\n"
            "Topic: [SPECIFIC TOPIC]\n"
            "Exam board / curriculum: [e.g. IB, A-Level, GCSE, University module]\n"
            "Exam format: [e.g. multiple choice / essays / problem sets]\n"
            "Time until exam: [WEEKS]\n\n"
            "Include:\n"
            "1. CORE CONCEPTS — 8–12 key ideas, each with a 2-sentence plain-English explanation\n"
            "2. KEY TERMS GLOSSARY — 15 terms with definitions\n"
            "3. WORKED EXAMPLES — 3 solved problems or annotated case studies\n"
            "4. COMMON MISTAKES — top 5 errors students make and how to avoid them\n"
            "5. MEMORY AIDS — mnemonics, diagrams, or frameworks where useful\n"
            "6. PREDICTED EXAM QUESTIONS — 5 likely questions with mark-scheme guidance\n"
            "7. 24-HOUR REVISION PLAN — hour-by-hour if exam is tomorrow\n\n"
            "Make this dense and useful, not padded. Every line should help me score marks."
        ),
        "tags": ["revision", "exam", "student", "study", "guide"],
        "is_premium": False,
    },

    # ── BUSINESS ─────────────────────────────────────────────────────────────
    {
        "title": "Investor Pitch Deck Narrative",
        "description": "Writes the full narrative and key messages for each slide of a Series A / seed investor pitch deck — structured around the standard 10-slide framework.",
        "category": PromptCategory.BUSINESS,
        "template_content": (
            "You are a venture-backed startup advisor. Write the complete pitch deck narrative for the following company:\n\n"
            "Company name: [COMPANY]\n"
            "One-liner: [WHAT YOU DO IN ONE SENTENCE]\n"
            "Stage: [Pre-seed / Seed / Series A]\n"
            "Industry: [INDUSTRY]\n"
            "Problem: [THE PROBLEM YOU SOLVE]\n"
            "Solution: [YOUR PRODUCT / APPROACH]\n"
            "Traction: [KEY METRICS — ARR, users, growth rate, logos]\n"
            "Market size: [TAM / SAM / SOM if known]\n"
            "Ask: [AMOUNT RAISING AND USE OF FUNDS]\n\n"
            "For each of the 10 slides, write:\n"
            "- Slide title\n"
            "- Key message (1 sentence — what the investor should think/feel)\n"
            "- Bullet points / data points to include\n"
            "- Narrative speaker notes (what you say out loud)\n\n"
            "Slides: Cover → Problem → Solution → Why Now → Market Size → Product → Traction → Business Model → Team → Ask\n\n"
            "Be specific. Replace every placeholder in [brackets] before using. Investors fund conviction, not vagueness."
        ),
        "tags": ["pitch", "startup", "investor", "business", "fundraising"],
        "is_premium": True,
    },
    {
        "title": "Job Description — Technical Role",
        "description": "Writes a compelling, bias-minimised job description for any technical role — covering the role overview, responsibilities, requirements, and company sell.",
        "category": PromptCategory.BUSINESS,
        "template_content": (
            "You are a talent strategist. Write a complete job description for the following role:\n\n"
            "Role title: [JOB TITLE]\n"
            "Company: [COMPANY NAME]\n"
            "Industry: [INDUSTRY]\n"
            "Team size: [TEAM SIZE]\n"
            "Reports to: [MANAGER TITLE]\n"
            "Location / remote policy: [LOCATION / REMOTE / HYBRID]\n"
            "Salary range: [RANGE] (optional)\n"
            "Must-have skills: [SKILL 1], [SKILL 2], [SKILL 3]\n"
            "Nice-to-have skills: [SKILL A], [SKILL B]\n"
            "Company culture in 3 words: [WORD 1], [WORD 2], [WORD 3]\n\n"
            "Structure:\n"
            "1. Opening hook — why this role matters and what impact it has (2–3 sentences, no corporate fluff)\n"
            "2. What you'll do — 6–8 outcome-oriented responsibilities (start each with a verb)\n"
            "3. What we're looking for — split into Must Have and Nice to Have\n"
            "4. What we offer — compensation, benefits, growth, culture (be specific)\n"
            "5. About us — 3 sentences max, no boilerplate\n\n"
            "Bias-minimise: avoid gendered language, avoid excessive years-of-experience requirements, focus on outcomes over credentials."
        ),
        "tags": ["hiring", "job-description", "business", "hr", "recruitment"],
        "is_premium": False,
    },
]


async def seed_templates() -> None:
    for item in TEMPLATES:
        exists = await PromptTemplate.find_one(PromptTemplate.title == item["title"])
        if not exists:
            await PromptTemplate(**item).insert()
