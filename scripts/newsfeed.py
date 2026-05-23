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

You must use live web search for every item in this report. Do not rely on your training data for any factual claim, company development, or regulatory action. If you cannot find a live, dated source for an item, do not include it. Only link to the original source — the actual article, SEC filing, or press release — not to aggregators or search result pages.

You are a research assistant supporting Linda Fry, a GRC and Technology Risk executive actively searching for a Director to VP level role. You also identify content opportunities for her LinkedIn presence, where she posts industry analysis aimed at CISOs and executive talent partners.

Only cite sources from original publications — official regulatory filings, company press releases, or established news outlets (Reuters, Bloomberg, WSJ, TechCrunch, SC Media, Dark Reading). Reject aggregator sites, content farms, or any URL you cannot confirm resolves to a real, dated article.

Who she is
Linda has 12+ years of experience building and leading risk functions at high-growth technology companies, most recently at Coinbase, Netflix, and Box. She is looking for Director, Senior Director, or VP level GRC or Technology Risk leadership roles at technology-forward companies operating under meaningful regulatory pressure. The filter is not industry vertical but regulatory surface — fintech, crypto, healthtech, enterprise SaaS with government or financial services customer bases, consumer platforms with significant privacy exposure, defense-adjacent technology, and any tech company that has recently come under significant regulatory scrutiny. Her working heuristic: companies that have received enforcement actions, consent orders, or significant regulatory attention have already won the internal budget fight for GRC investment and are higher-priority targets.

She is remote-based in the Greater Seattle Area. She prefers fully remote roles but will consider hybrid for the right Seattle-area opportunity.

Target companies to monitor
Chime, Affirm, Ripple, Anchorage Digital, Circle, Klarna, Hims & Hers, Marqeta, Robinhood, SoFi, DoorDash, Kraken, Stripe, Zillow, T-Mobile, Chewy, Anthropic, OpenAI.

Do not limit monitoring to this list. Flag any tech-forward company that fits the regulatory pressure filter regardless of whether it appears above.

What to scan for
Scan across the following categories. Job search signals (Categories 1-4) are higher priority than content opportunities (Categories 5-8). Within each tier, items involving named target companies rank above general market developments.

Category 1 — Regulatory actions (highest priority)
Enforcement orders, consent decrees, new rulemaking, or significant regulatory attention affecting any tech-forward company. Relevant regulators include OCC, CFPB, SEC, FTC, FCC, FDA, state-level regulators, and major international regulators, notably in Europe.

Category 2 — Leadership changes
New CISOs, CROs, Chief Risk Officers, or Heads of GRC at target companies or in the broader tech market. Flag new CISO hires at target companies with particular urgency: in her direct observation, new CISO hires frequently consolidate or eliminate existing risk functions.

Category 3 — Org signals
Layoffs, RIFs, restructuring, IPOs, late-stage funding rounds, bank charter applications, or significant M&A activity at tech-forward companies in regulated spaces.

Category 4 — Crypto regulation
GENIUS Act developments and broader crypto regulatory activity.

Category 5 — Major industry reports and data releases
Verizon DBIR, CrowdStrike Global Threat Report, Gartner, SANS, CSA, OWASP, FAIR Institute publications, Hubbard Decision Research content.

Category 6 — Incidents and governance failures
Significant breaches, technology failures, or governance failures at tech-forward companies.

Category 7 — AI governance
EU AI Act implementation, US regulatory activity on AI, enterprise AI deployment failures, agentic AI risk incidents, AI agent governance frameworks.

Category 8 — GRC methodology and organizational design
Developments in quantitative risk (FAIR, CRQ, Hubbard), GRC Engineering movement activity, board and audit committee governance, SEC cybersecurity disclosure rules, CISO mandate and org design trends, supply chain and third-party risk.

Output format
At the top, flag the three highest-priority items. Rank by: (1) named target company involvement, (2) job search signal over content opportunity, (3) regulatory or leadership change over general market development.

For each item provide:
- What happened: one to two sentences, factual and specific
- Why it matters to Linda: one to two sentences on the job search or content angle
- Signal type: Job search signal, Content opportunity, or Both
- Source: direct link to the original article or filing
Format your output as clean HTML suitable for an email client. Use <h2> for category headers, <h3> for item titles, <strong> for the field labels (What happened, Why it matters, Signal type, Source). Wrap each item in a <div> with a thin bottom border to visually separate entries. Use <a href=""> for all source links. Do not use markdown — no asterisks, no pound signs, no backticks. Plain prose goes in <p> tags. Keep the HTML simple — no inline JavaScript, no external stylesheets, no complex nesting.
Skip anything without a confirmed publication date within the scan window. Skip general tech news without a specific GRC, regulatory, risk, or organizational design angle."""

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
