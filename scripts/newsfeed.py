import anthropic
import nh3
import re
import smtplib
import os
import sys
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# The report is built from live web-search results, which are untrusted input.
# A malicious page can attempt indirect prompt injection to make the model emit
# tracking beacons (<img>), scripts, or javascript:/data: links that would fire
# or exfiltrate when the email is opened. We never trust the model output as
# safe HTML — it is run through an allowlist sanitizer before being emailed.
# Only these tags/attributes survive; everything else (img, script, style,
# iframe, event handlers, non-http(s)/mailto URLs) is stripped.
ALLOWED_TAGS = {"h2", "h3", "p", "strong", "em", "ul", "ol", "li", "div", "a", "br"}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}
ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}


def sanitize_html(html):
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
    )


# Approximate published Opus rates, in USD per token. Adjust if pricing changes
# — these only drive the logged cost estimate, not anything functional.
PRICE_INPUT = 15 / 1_000_000          # fresh (uncached) input
PRICE_CACHE_WRITE = 18.75 / 1_000_000  # cache creation = 1.25x input
PRICE_CACHE_READ = 1.5 / 1_000_000     # cache read = 0.1x input
PRICE_OUTPUT = 75 / 1_000_000
PRICE_WEB_SEARCH = 10 / 1_000          # $10 per 1,000 searches


def log_usage(usage):
    """Print real token/search usage and an estimated dollar cost to the run log."""
    fresh_in = getattr(usage, "input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    out = getattr(usage, "output_tokens", 0) or 0
    server_tool = getattr(usage, "server_tool_use", None)
    searches = getattr(server_tool, "web_search_requests", 0) or 0 if server_tool else 0

    est_cost = (
        fresh_in * PRICE_INPUT
        + cache_write * PRICE_CACHE_WRITE
        + cache_read * PRICE_CACHE_READ
        + out * PRICE_OUTPUT
        + searches * PRICE_WEB_SEARCH
    )

    print(
        "Usage — "
        f"input(fresh): {fresh_in:,}, cache write: {cache_write:,}, "
        f"cache read: {cache_read:,}, output: {out:,}, web searches: {searches:,}\n"
        f"Estimated cost: ${est_cost:.2f} "
        "(rate estimate; verify against Anthropic pricing)"
    )


def get_newsfeed():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%B %d, %Y")

    prompt = f"""Today's date is {today}. The scan window is {week_ago} through {today}. Only include items published within this window. Verify the publication date of every source before including it — reject anything outside the scan window.

You must use live web search for every item in this report. Do not rely on your training data for any factual claim, company development, or regulatory action. If you cannot find a live, dated source for an item, do not include it. Only link to the original source — the actual article, SEC filing, or press release — not to aggregators or search result pages. Try to avoid sites whose content is behind a paywall.

If a category yields no confirmed items this week, output the category header followed by: "Nothing confirmed this week." Do not fill empty categories with soft sources or loosely relevant items.

You are a research assistant supporting Linda Fry, a GRC and Technology Risk executive actively searching for a Director to VP level role. You also identify content opportunities for her LinkedIn presence, where she posts industry analysis aimed at CISOs and executive talent partners.

Only cite sources from original publications — official regulatory filings, company press releases, or established news outlets (Reuters, Bloomberg, WSJ, TechCrunch, SC Media, Dark Reading). Also draw directly from: FDIC and OCC enforcement action databases, SEC EDGAR full-text search for cybersecurity disclosure filings, and FinCEN for anything touching crypto or financial services clients. Reject aggregator sites, content farms, or any URL you cannot confirm resolves to a real, dated article.

---

WHO SHE IS

Linda has 12+ years of experience building and leading risk functions at high-growth technology companies, most recently at Coinbase, Netflix, and Box. She is looking for Director, Senior Director, or VP level GRC or Technology Risk or Chief Risk leadership roles at technology-forward companies in regulated verticals. The filter prioritizes regulatory surface over industry vertical: fintech, crypto, healthtech, AI, enterprise SaaS with government contracts, life sciences, financial services, consumer platforms with significant privacy exposure, and defense-adjacent technology all fit the profile. Within these verticals, companies that have received enforcement actions, consent orders, or significant regulatory attention are higher-priority targets, but any company in a regulated vertical is in scope.

She is remote-based in the Greater Seattle Area. She prefers fully remote roles but will consider hybrid for the right Seattle-area opportunity.

---

TARGET COMPANIES TO MONITOR

Chime, Affirm, Ripple, Anchorage Digital, Circle, Klarna, Hims & Hers, Marqeta, Robinhood, SoFi, DoorDash, Kraken, Stripe, Zillow, T-Mobile, Chewy, Anthropic, OpenAI.

Do not limit monitoring to this list. Flag any tech-forward company in a regulated vertical — fintech, crypto, healthtech, AI, enterprise SaaS with government contracts, life sciences, financial services, consumer platforms with significant privacy exposure, defense-adjacent technology — regardless of whether it appears above. Companies with recent enforcement actions or regulatory attention are higher-priority, but regulated-vertical membership alone is sufficient to include a company.

---

SCAN CATEGORIES AND PRIORITY ORDER

Category 0 and Categories 1 through 3 are job search signals and take priority over Categories 4 through 7, which are content opportunities. Within each tier, items involving named target companies rank above general market developments.

CATEGORY 0 — OPEN ROLES (highest priority, run first)

Search LinkedIn, Greenhouse, Lever, Ashby, and company career pages for active job postings matching Director, Senior Director, or VP level GRC, Technology Risk, or Enterprise Risk roles at target companies and close analogs. Prioritize companies in regulated verticals that are in IPO preparation or approaching IPO within the next 18 months — these are high-signal hiring windows where GRC investment is most active. Look for companies that have announced IPO plans, filed for IPO, received late-stage funding tied to IPO preparation, or are publicly known to be preparing for public markets within this timeframe.

In addition to direct company career pages, scan the following venture-capital portfolio job boards, which aggregate openings across each firm's portfolio companies. These are high-yield for Linda because portfolio companies skew toward high-growth, tech-forward businesses operating under meaningful regulatory pressure. On each board, filter for Director, Senior Director, or VP level GRC, Technology Risk, Enterprise Risk, or Chief Risk roles that fit the regulatory-pressure profile described above. Treat each URL as a starting point only: if a board has moved or a link returns an error, locate that firm's current portfolio or talent job board by web search before giving up. These boards are aggregators, so use them to discover roles, not as Source links — when you find a matching role, follow through to the underlying company posting (its Greenhouse, Lever, Ashby, or career-page listing) and cite that live, role-specific page as the Source; only if no underlying posting exists should you cite the board's role-specific detail page. Never cite a board's index, listing, or search page as a Source. Apply the same live-link verification rules described below to every role before listing it.

- Andreessen Horowitz (a16z): https://portfoliojobs.a16z.com
- Index Ventures: https://jobs.indexventures.com
- General Catalyst: https://jobs.generalcatalyst.com
- Khosla Ventures: https://jobs.khoslaventures.com
- Sequoia Capital: https://jobs.sequoiacap.com
- Greylock Partners: https://jobs.greylock.com
- Kleiner Perkins: https://jobs.kleinerperkins.com
- BITKRAFT Ventures: https://bitkraft.vc/jobs
- Accel: https://jobs.accel.com
- Y Combinator (Work at a Startup): https://www.workatastartup.com
- Contrary: https://jobs.contrary.com
- Pear VC: https://jobs.pear.vc
- Battery Ventures: https://jobs.battery.com
- New Enterprise Associates (NEA): https://jobs.nea.com
- Antler: https://jobs.antler.co
- Lightspeed Venture Partners: https://jobs.lsvp.com/jobs
- Bessemer Venture Partners: https://jobs.bvp.com/jobs

The 7-day scan window above does NOT apply to this category. Roles are governed by whether they are currently live, not by when they were first posted. A still-open role posted three weeks ago is in scope; a role posted yesterday that has already closed is not.

Every posting you include must be currently live and open to applications. Search results and search-engine snippets routinely surface roles that have already been filled or closed, so a search hit is not sufficient evidence that a role is open. Before including any role, open the posting page itself and confirm from its content that it is still accepting applications.

A page that returns successfully is NOT proof the role is live. Closed postings very frequently still "work" but silently redirect to the company's default careers homepage, a job-search index, or a generic "open positions" listing, while the original link continues to resolve. You must confirm that the final page you land on actually displays that exact role — its specific title and description, with an active apply control. If the link instead lands on a careers homepage, a job-search or "open positions" index, a search results page, or a "job not found" / "this position is no longer available" page, the role is dead — exclude it. The link you put in the Source field must point to that live, role-specific detail page, not to a redirect target or a careers landing page.

Reject the posting — do not list it — if any of the following are true: the page does not load or returns an error; the link redirects to or lands on a generic careers page, job-search index, or listing rather than the specific role's detail page; the final page does not display that exact role's title and description with an active apply control; the page states the role is closed, filled, paused, on hold, expired, or "no longer accepting applications"; the listing shows no posting or last-refreshed date; or the posting date is more than 30 days before today. When in doubt, exclude rather than guess: an omitted role is fine, a dead role is the failure mode to avoid.

For each confirmed role, provide the role title, company, the posting or last-refreshed date exactly as it appears on the page, and a direct link to the role-specific posting itself (not a search results page, careers homepage, or job-aggregator listing). Note whether the company has appeared in any other category this week, as co-occurrence is a strong signal. If the company is in IPO preparation or publicly known to be approaching IPO within 18 months, flag this prominently — it is a high-priority hiring signal. If you cannot confirm a single live role this week, output: "Nothing confirmed this week."

For every confirmed role, note its location and work arrangement (remote, hybrid, or onsite) as stated on the posting. If the role's primary location is outside the Greater Seattle Area, additionally flag the company's current work-location posture: whether it has recently announced or enforced a significant Return-to-Office (RTO) mandate, or whether it is genuinely remote-friendly. Base this on dated, verifiable sources — the posting's own remote/location terms, a company announcement, or recent news coverage — and say so briefly if you cannot confirm either way. This flag is informational only: do NOT exclude, downrank, or filter out an otherwise relevant out-of-area role because of an RTO push or because the work arrangement is unclear. Linda still wants to see these roles; the flag simply tells her what she would be walking into. Roles based in the Greater Seattle Area, or explicitly advertised as fully remote, do not need the RTO research.

CATEGORY 1 — REGULATORY ACTIONS

Enforcement orders, consent decrees, new rulemaking, or significant regulatory attention affecting any tech-forward company. Relevant regulators include OCC, CFPB, SEC, FTC, FCC, FDA, FDIC, FinCEN, state-level regulators, and major international regulators, notably in Europe.

CATEGORY 2 — ORG SIGNALS

Layoffs, RIFs, restructuring, IPOs, late-stage funding rounds, bank charter applications, or significant M&A activity at tech-forward companies in regulated spaces. For each item, assign a hiring window temperature: Hot (company is likely actively building the function — e.g., post-enforcement action, post-funding, new CISO in seat), Warm (conditions are favorable but timing is uncertain), Cold (company is mid-restructure or in a hiring freeze), or Avoid (signals suggest Linda should not prioritize this target right now, with a brief reason).

CATEGORY 3 — CRYPTO REGULATION

GENIUS Act developments and broader crypto regulatory activity.

CATEGORY 4 — MAJOR INDUSTRY REPORTS AND DATA RELEASES

Scan broadly across major industry data releases and the technology and cybersecurity think tanks, research centers, and standards bodies listed below. Include a new report, framework update, dataset, or publication only when it carries a clear angle relevant to Governance, Risk, and Compliance or AI Governance — skip purely technical or operational releases with no GRC, risk-quantification, board-governance, regulatory, or AI-governance relevance.

Core data releases: Verizon DBIR, CrowdStrike Global Threat Report, Gartner, SANS, CSA, FAIR Institute publications, Hubbard Decision Research content.

Think tanks and research centers: Center for Security and Emerging Technology (CSET), Institute for AI Policy and Strategy (IAPS), Institute for Security and Technology (IST), Institute for Critical Infrastructure Technology (ICIT), UC Berkeley Center for Long-Term Cybersecurity.

Standards bodies and frameworks: NIST Cybersecurity Framework (CSF), NIST Trustworthy & Responsible AI Resource Center, ISO 27001, CIS Critical Security Controls, ISACA, MITRE Corporation, OWASP, PCI Security Standards Council (PCI SSC), HITRUST. Flag new releases, framework revisions, draft guidance, or notable commentary from these bodies when they bear on GRC or AI governance.

CATEGORY 5 — INCIDENTS AND GOVERNANCE FAILURES

Significant breaches, technology failures, or governance failures at tech-forward companies.

CATEGORY 6 — AI GOVERNANCE

EU AI Act implementation, US regulatory activity on AI, enterprise AI deployment failures, agentic AI risk incidents, AI agent governance frameworks. Prioritize items involving agentic AI risk failures, enterprise AI deployment governance gaps, and regulatory action touching AI deployment in financial services or healthtech specifically. These intersect directly with Linda's positioning as an AI-native GRC leader.

CATEGORY 7 — GRC METHODOLOGY AND ORGANIZATIONAL DESIGN

Developments in quantitative risk (FAIR, CRQ, Hubbard, ERQI), GRC Engineering movement activity, board and audit committee governance, SEC cybersecurity disclosure rules, CISO mandate and org design trends, supply chain and third-party risk.

---

OUTPUT FORMAT

Begin your response with the opening HTML tag. Do not narrate your search process, describe your methodology, summarize what you are about to do, or include any preamble or transitional language before the HTML output. The report starts with the HTML — nothing before it.
At the top of the report, flag the three highest-priority items across all categories. Rank by: (1) named target company involvement, (2) open role or job search signal over content opportunity, (3) regulatory action over general market development.

For each item in Categories 0 through 3, provide:
- What happened: one to two sentences, factual and specific.
- Why it matters to Linda: one to two sentences on the job search or content angle.
- Recommended action: a specific next step and, where relevant, a time window. 
- Signal type: Job search signal, Content opportunity, or Both.
- Hiring window temperature (Categories 0 and 2 only): Hot, Warm, Cold, or Avoid, with a one-sentence rationale.
- Location and work arrangement (Category 0 only): the role's location and whether it is remote, hybrid, or onsite. For roles outside the Greater Seattle Area, also flag whether the company has a recent Return-to-Office (RTO) push or is remote-friendly, with the basis for that flag. This is informational and never a reason to omit the role.
- IPO status (Category 0 only, if applicable): whether the company is in IPO preparation or approaching IPO within 18 months, with the basis (announced plans, S-1 filing, recent funding, public news).
- Source: direct link to the original article, filing, or job posting.

For each item in Categories 4 through 7, provide:
- What happened: one to two sentences, factual and specific.
- Why it matters to Linda: one to two sentences on the content angle.
- Signal type: Content opportunity, Job search signal, or Both.
- Source: direct link to the original article or filing.

When flagging errors and limitations, apply the following rules throughout the report.
If a source is paywalled or only partially accessible, include the item but add a note in the Source field: "Paywalled — summary based on headline and visible excerpt only. Verify before acting."
If a hiring window temperature assessment in Category 2 is based on a single signal or thin evidence, add a note after the temperature rating: "Low confidence — based on limited signal."
If a job posting in Category 0 cannot be confirmed as currently live and accepting applications by opening the posting page, exclude it entirely. Do not list unverified or stale roles even with a caveat — in this category a wrong listing is worse than an omission.
If two or more sources report the same event with conflicting details, include the item but note the conflict: "Conflicting reports — see sources." and provide both links.
If web search returns no results for a specific target company in a given category, do not infer absence of news. Note it as: "No confirmed results found for [company] this week — coverage may be incomplete."
At the end of the report, include a final section titled THIS WEEK'S RECOMMENDED POST. Select the single strongest LinkedIn content opportunity from the week's scan. Specify whether it is a thinky post (industry POV, analytical) or a human/leadership post (warmer, story-driven). Provide a one-sentence opening claim that Linda could use or adapt as the post's opening line. Do not write the full post — just the angle, the type, and the opening hook.

Format the full output as clean HTML suitable for an email client. Use <h2> for category headers, <h3> for item titles, <strong> for field labels. Wrap each item in a <div> with a thin bottom border. Use <a href=""> for all source links. Do not use markdown. Plain prose goes in <p> tags. Keep the HTML simple — no inline JavaScript, no external stylesheets, no complex nesting.
"""

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=32000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        # Cache the large static prompt. The web-search tool loop makes many
        # model turns within this single call, and each turn would otherwise
        # reprocess the full prompt at full input price; caching it means
        # turns after the first read the prefix from cache at ~10% the cost.
        messages=[{
            "role": "user",
            "content": [{
                "type": "text",
                "text": prompt,
                "cache_control": {"type": "ephemeral"},
            }],
        }],
    )

    log_usage(message.usage)

    # If the model hit the output cap, the report is truncated mid-section.
    # Surface it instead of emailing a half-complete newsletter.
    if message.stop_reason == "max_tokens":
        raise ValueError(
            "Model response was truncated at the max_tokens limit; "
            "raise max_tokens. Report not sent."
        )

    # Extract all text blocks from the response (tool use returns mixed content)
    text_parts = [block.text for block in message.content if hasattr(block, "text")]
    full_text = "\n\n".join(text_parts)

    # During web search the model emits text blocks narrating each search before
    # producing the report. Drop everything before the first HTML tag so only the
    # report itself is emailed.
    match = re.search(
        r"<(?:!doctype|html|head|body|h[1-6]|div|p|ul|ol|table|section)\b",
        full_text,
        re.IGNORECASE,
    )
    if not match:
        # No HTML report was produced (e.g. the model only narrated, or the call
        # returned empty). Fail loudly rather than emailing raw search narration.
        raise ValueError("Model response contained no HTML report; nothing to send.")

    # Sanitize before returning: web-search content is untrusted and the model's
    # output is not a trusted source of safe HTML (see sanitize_html above).
    report = sanitize_html(full_text[match.start():])
    if not report.strip():
        raise ValueError("Report was empty after sanitization; nothing to send.")
    return report

def send_email(body):
    sender = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = sender
    msg["Subject"] = f"Weekly Tech Intel Newsfeed — {datetime.now(timezone.utc).strftime('%B %d, %Y')}"
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, app_password)
        server.sendmail(sender, sender, msg.as_string())

if __name__ == "__main__":
    try:
        newsfeed = get_newsfeed()
        send_email(newsfeed)
    except Exception as exc:
        # Exit non-zero so the GitHub Action surfaces the failure instead of
        # reporting a green run after a bad or missing send.
        print(f"Newsfeed run failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print("Sent successfully.")
