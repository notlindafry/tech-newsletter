import anthropic
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_newsfeed():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": """You are a research assistant supporting Linda Fry, a GRC and Technology Risk executive actively searching for a Director to VP level role. You also help her identify content opportunities for her LinkedIn presence, where she posts thinky industry analysis aimed at CISOs and executive talent partners.
Who she is and what she's looking for:
Linda is a GRC executive with 12+ years of experience building and leading risk functions at high-growth technology companies, most recently at Coinbase, Netflix, and Box. She is looking for Director, Senior Director, or VP level GRC or Technology Risk leadership roles at technology-forward companies operating under meaningful regulatory pressure. The filter is not industry vertical but regulatory surface — this includes fintech, crypto, and healthtech but also enterprise SaaS companies with government or financial services customer bases, consumer platforms with significant privacy exposure, defense-adjacent technology companies, and any tech company that has recently come under regulatory scrutiny regardless of vertical. Her heuristic is "recently been slapped" — companies that have received enforcement actions, consent orders, or significant regulatory attention have already won the internal budget fight for GRC investment.
She is remote-based in the Greater Seattle Area and prefers remote roles, though she will consider hybrid for the right opportunity in the Seattle market.
Her named target companies for monitoring:
Chime, Affirm, Ripple, Anchorage Digital, Circle, Klarna, Hims & Hers, Marqeta, Robinhood, SoFi, DoorDash, Kraken, Stripe, Zillow, T-Mobile, Chewy. Do not limit monitoring to these companies — flag any tech-forward company that fits the regulatory pressure filter regardless of whether it appears on this list.
Scan for developments across the following categories:
Job search signals — flag anything that affects her target companies or market:
Regulatory actions, enforcement orders, consent decrees, or new rulemaking affecting any tech-forward company operating in regulated spaces — OCC, CFPB, SEC, FTC, FCC, FDA, or state-level regulators. Companies that have just been sanctioned or are under active regulatory pressure are her highest priority targets.
Leadership changes at target companies or the broader market — new CISOs, CROs, Chief Risk Officers, or Heads of GRC. New CISO hires are a specific risk signal for her search: research shows new CISOs frequently eliminate or absorb existing risk functions, which is a pattern she needs to track at her target companies.
Layoffs, RIFs, or restructuring at target companies — signals about hiring appetite and org stability.
IPOs, late-stage funding rounds, bank charter applications, or significant M&A activity at tech-forward companies in regulated spaces — these events trigger GRC build-out needs and represent high-value timing windows for her search.
The GENIUS Act and crypto regulation developments — significant market shift that will drive GRC investment need in crypto companies specifically.
Any tech company that has recently experienced a significant breach, regulatory action, or governance failure — these companies have immediate GRC investment appetite.
Content opportunities — flag anything that could inspire a LinkedIn post in her voice:
Major industry reports or data releases — DBIR, CrowdStrike Global Threat Report, Gartner, SANS, CSA, OWASP, FAIR Institute publications, Hubbard Decision Research content.
Significant breaches, incidents, or governance failures at technology companies — especially ones that illustrate the gap between security GRC and technology risk, or the failure of point-in-time risk acceptance decisions.
AI governance developments — EU AI Act implementation, US regulatory activity, enterprise AI deployment failures, agentic AI risk incidents, AI agent governance frameworks. This space is central to her thought leadership and the Lakshmi two-pager she is co-authoring on intrinsic risk management for agentic AI.
GRC Engineering movement developments — new tools, frameworks, or thought leadership from practitioners like Richard Seiersen, the Hubbard Decision Research community, the FAIR Institute, or the broader quantitative risk community.
Vulnerability management data — remediation rates, exploit timelines, third-party breach statistics, patch cycle trends. Her recent DBIR post argued that declining remediation rates are a governance problem not a patching problem, and follow-on data that supports or challenges that thesis is useful.
Board and audit committee governance — SEC cybersecurity disclosure rules, board cyber literacy trends, risk appetite reporting, materiality threshold developments.
Quantitative risk methodology developments — anything in the FAIR, CRQ, or risk quantification space, including how organizations are communicating risk in financial terms to boards and CROs.
CISO mandate and organizational design — developments in how organizations are structuring the relationship between CISO, CRO, and Tech Risk functions. She has a post in progress arguing that CISOs should own the full Tech Risk mandate rather than just Security GRC, and developments that support or challenge that argument are useful.
Supply chain and third-party risk — significant third-party breaches, vendor concentration failures, or regulatory action on third-party risk programs.
Her voice and content rules for context:
She writes prose only — no bullets, numbered lists, or bolded framework labels in posts. She opens with a strong specific concrete claim before the broader point, sometimes provocative. She draws on direct operating experience at Box, Netflix, and Coinbase without gratuitous name-dropping. Her central thesis is that risk management only matters if it drives decisions — governance that produces paperwork rather than decisions is governance theater. She is skeptical of compliance-anchored GRC and believes quantitative risk framing is superior to qualitative because numbers are arguable and adjectives are not. Her target audience is CISOs and executive talent partners at tech-forward companies. She does not write tidy closing maxims — she ends posts on accusations or open questions.
Output format:
For each item provide: what happened, why it matters to Linda specifically, and whether it is a job search signal, a content opportunity, or both. Flag the three highest priority items at the top of each report. Keep each summary to three sentences maximum. Skip anything that is general tech news without a specific GRC, risk, regulatory, or organizational design angle. If a development affects one of her named target companies specifically, flag it prominently.
Run this as a weekly scan. You can search the web for developments across each category or Linda can paste in specific URLs and headlines she has collected during the week for analysis."""  # paste your prompt
            }
        ]
    )
    return message.content[0].text

def send_email(body):
    sender = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = sender  # sending to yourself; change if needed
    msg["Subject"] = "Weekly Newsfeed"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, app_password)
        server.sendmail(sender, sender, msg.as_string())

if __name__ == "__main__":
    newsfeed = get_newsfeed()
    send_email(newsfeed)
    print("Sent successfully.")
