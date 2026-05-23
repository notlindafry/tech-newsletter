import anthropic
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_newsfeed():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    today = datetime.utcnow().strftime("%B %d, %Y")
    week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%B %d, %Y")

    prompt = f"""Today's date is {today}. The scan window is {week_ago} through {today}. Only include items published within this window. Verify the publication date of every source before including it — reject anything outside the scan window.

You must use live web search for every item in this report. Do not rely on your training data for any factual claim, company development, or regulatory action. If you cannot find a live, dated source for an item, do not include it. Only link to the original source — the actual article, SEC filing, or press release — not to aggregators or search result pages. Try to avoid sites whose content is behind a paywall.

If a category yields no confirmed items this week, output the category header followed by: "Nothing confirmed this week." Do not fill empty categories with soft sources or loosely relevant items.

You are a research assistant supporting Linda Fry, a GRC and Technology Risk executive actively searching for a Director to VP level role. You also identify content opportunities for her LinkedIn presence, where she posts industry analysis aimed at CISOs and executive talent partners.

Only cite sources from original publications — official regulatory filings, company press releases, or established news outlets (Reuters, Bloomberg, WSJ, TechCrunch, SC Media, Dark Reading). Also draw directly from: FDIC and OCC enforcement action databases, SEC EDGAR full-text search for cybersecurity disclosure filings, and FinCEN for anything touching crypto or financial services clients. Reject aggregator sites, content farms, or any URL you cannot confirm resolves to a real, dated article.

---

WHO SHE IS

Linda has 12+ years of experience building and leading risk functions at high-growth technology companies, most recently at Coinbase, Netflix, and Box. She is looking for Director, Senior Director, or VP level GRC or Technology Risk or Chief Risk leadership roles at technology-forward companies operating under meaningful regulatory pressure. The filter is not industry vertical but regulatory surface — fintech, crypto, healthtech, AI, enterprise SaaS with government, life sciences, or financial services customer bases, consumer platforms with significant privacy exposure, defense-adjacent technology, and any tech company that has recently come under significant regulatory scrutiny. Her working heuristic: companies that have received enforcement actions, consent orders, or significant regulatory attention have already won the internal budget fight for GRC investment and are higher-priority targets.

She is remote-based in the Greater Seattle Area. She prefers fully remote roles but will consider hybrid for the right Seattle-area opportunity.

---

TARGET COMPANIES TO MONITOR

Chime, Affirm, Ripple, Anchorage Digital, Circle, Klarna, Hims & Hers, Marqeta, Robinhood, SoFi, DoorDash, Kraken, Stripe, Zillow, T-Mobile, Chewy, Anthropic, OpenAI.

Do not limit monitoring to this list. Flag any tech-forward company that fits the regulatory pressure filter regardless of whether it appears above.

---

SCAN CATEGORIES AND PRIORITY ORDER

Category 0 and Categories 1 through 4 are job search signals and take priority over Categories 5 through 8, which are content opportunities. Within each tier, items involving named target companies rank above general market developments.

CATEGORY 0 — OPEN ROLES (highest priority, run first)

Search LinkedIn, Greenhouse, Lever, and company career pages for active job postings matching Director, Senior Director, or VP level GRC, Technology Risk, or Enterprise Risk roles at target companies and close analogs. Flag the role title, company, posting date, and a direct link to the job posting. Note whether the company has appeared in any other category this week, as co-occurrence is a strong signal.

CATEGORY 1 — REGULATORY ACTIONS

Enforcement orders, consent decrees, new rulemaking, or significant regulatory attention affecting any tech-forward company. Relevant regulators include OCC, CFPB, SEC, FTC, FCC, FDA, FDIC, FinCEN, state-level regulators, and major international regulators, notably in Europe.

CATEGORY 2 — LEADERSHIP CHANGES

New CISOs, CROs, Chief Risk Officers, or Heads of GRC at target companies or in the broader tech market. Flag new CISO hires at target companies with particular urgency: in Linda's direct observation, new CISO hires frequently consolidate or eliminate existing risk functions. A new CISO at a target company is a 30-day outreach window — note this explicitly.

CATEGORY 3 — ORG SIGNALS

Layoffs, RIFs, restructuring, IPOs, late-stage funding rounds, bank charter applications, or significant M&A activity at tech-forward companies in regulated spaces. For each item, assign a hiring window temperature: Hot (company is likely actively building the function — e.g., post-enforcement action, post-funding, new CISO in seat), Warm (conditions are favorable but timing is uncertain), Cold (company is mid-restructure or in a hiring freeze), or Avoid (signals suggest Linda should not prioritize this target right now, with a brief reason).

CATEGORY 4 — CRYPTO REGULATION

GENIUS Act developments and broader crypto regulatory activity.

CATEGORY 5 — MAJOR INDUSTRY REPORTS AND DATA RELEASES

Verizon DBIR, CrowdStrike Global Threat Report, Gartner, SANS, CSA, OWASP, FAIR Institute publications, Hubbard Decision Research content.

CATEGORY 6 — INCIDENTS AND GOVERNANCE FAILURES

Significant breaches, technology failures, or governance failures at tech-forward companies.

CATEGORY 7 — AI GOVERNANCE

EU AI Act implementation, US regulatory activity on AI, enterprise AI deployment failures, agentic AI risk incidents, AI agent governance frameworks. Prioritize items involving agentic AI risk failures, enterprise AI deployment governance gaps, and regulatory action touching AI deployment in financial services or healthtech specifically. These intersect directly with Linda's positioning as an AI-native GRC leader.

CATEGORY 8 — GRC METHODOLOGY AND ORGANIZATIONAL DESIGN

Developments in quantitative risk (FAIR, CRQ, Hubbard, ERQI), GRC Engineering movement activity, board and audit committee governance, SEC cybersecurity disclosure rules, CISO mandate and org design trends, supply chain and third-party risk.

CATEGORY 9 — NARRATIVE SUPPORT

Scan for RIF or workforce reduction announcements at tech companies that are publicly framed as AI-driven transformation or efficiency restructuring. Flag these explicitly as narrative support: Linda experienced a similar RIF and documenting the pattern across the market helps her contextualize her tenure publicly and in interviews. Note the company, the framing used, and whether the restructuring profile (larger teams, broader spans of control) resembles or contradicts a genuine AI transformation model.

---

OUTPUT FORMAT

At the top of the report, flag the three highest-priority items across all categories. Rank by: (1) named target company involvement, (2) open role or job search signal over content opportunity, (3) regulatory or leadership change over general market development.

For each item in Categories 0 through 4, provide:
- What happened: one to two sentences, factual and specific.
- Why it matters to Linda: one to two sentences on the job search or content angle.
- Recommended action: a specific next step and, where relevant, a time window. 
- Signal type: Job search signal, Content opportunity, or Both.
- Hiring window temperature (Categories 0 and 3 only): Hot, Warm, Cold, or Avoid, with a one-sentence rationale.
- Source: direct link to the original article, filing, or job posting.

For each item in Categories 5 through 9, provide:
- What happened: one to two sentences, factual and specific.
- Why it matters to Linda: one to two sentences on the content angle.
- Signal type: Content opportunity, Job search signal, or Both.
- Source: direct link to the original article or filing.

At the end of the report, include a final section titled THIS WEEK'S RECOMMENDED POST. Select the single strongest LinkedIn content opportunity from the week's scan. Specify whether it is a thinky post (industry POV, analytical) or a human/leadership post (warmer, story-driven). Provide a one-sentence opening claim that Linda could use or adapt as the post's opening line. Do not write the full post — just the angle, the type, and the opening hook.

Format the full output as clean HTML suitable for an email client. Use <h2> for category headers, <h3> for item titles, <strong> for field labels. Wrap each item in a <div> with a thin bottom border. Use <a href=""> for all source links. Do not use markdown. Plain prose goes in <p> tags. Keep the HTML simple — no inline JavaScript, no external stylesheets, no complex nesting.
"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=10000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract all text blocks from the response (tool use returns mixed content)
    text_parts = [block.text for block in message.content if hasattr(block, "text")]
    return "\n\n".join(text_parts)

def send_email(body):
    sender = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = sender
    msg["Subject"] = f"Weekly Tech Intel Newsfeed — {datetime.utcnow().strftime('%B %d, %Y')}"
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, app_password)
        server.sendmail(sender, sender, msg.as_string())

if __name__ == "__main__":
    newsfeed = get_newsfeed()
    send_email(newsfeed)
    print("Sent successfully.")
