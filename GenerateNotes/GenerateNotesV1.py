import pandas as pd
from datetime import datetime, timedelta
import random

# Load data
df = pd.read_csv('Sales-Opportunity-Data.csv')  # Your full file

# Parse dates
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%d-%m-%Y')
    except:
        return None

df['engage_date'] = df['deal_engage_date'].apply(parse_date)
df['close_date'] = df['deal_close_date'].apply(parse_date)

def generate_notes(row):
    engage = row['engage_date']
    close = row['close_date']
    if engage is None or close is None:
        return "Invalid dates; no notes generated."
    
    days = (close - engage).days
    if days <= 0:
        return "Deal closed immediately upon engagement."
    
    # Sector-based roles (expanded to 5-7 per sector)
    sector = row['account_sector'].lower()
    product = row['product']
    account = row['account_name']
    stage = row['deal_stage']
    sales_rep = row['sales_rep']
    
    role_options = {
        'medical': ['CTO', 'Project Manager', 'Clinical Director', 'Sponsor', 'Compliance Officer', 'Chief Medical Officer', 'IT Director'],
        'retail': ['Procurement Manager', 'Business Analyst', 'Operations Lead', 'CEO', 'Merchandising Director', 'Supply Chain Manager', 'Customer Experience Lead'],
        'software': ['CTO', 'Product Manager', 'DevOps Engineer', 'Sponsor', 'Software Architect', 'QA Lead', 'Engineering Manager'],
        'services': ['Account Executive', 'Operations Manager', 'Business Development Lead', 'Service Delivery Director', 'Client Success Manager', 'HR Partner'],
        'entertainment': ['Creative Director', 'Technical Producer', 'Marketing Head', 'Content Strategist', 'Talent Manager', 'Distribution Executive', 'Audience Insights Analyst'],
        'telecommunications': ['Network Architect', 'IT Director', 'Procurement Specialist', 'Customer Operations Lead', '5G Strategy Manager', 'Data Analytics Head'],
        'finance': ['CFO', 'Risk Analyst', 'Compliance Officer', 'Sponsor', 'Treasury Manager', 'Investment Director', 'Regulatory Affairs Lead'],
        'employment': ['HR Director', 'Talent Acquisition Lead', 'Operations Manager', 'Diversity Officer', 'Learning & Development Head', 'Recruitment Specialist'],
        'marketing': ['CMO', 'Digital Strategist', 'Campaign Manager', 'Brand Director', 'Analytics Lead', 'Content Creator', 'SEO Specialist'],
        'technolgy': ['CTO', 'Systems Engineer', 'Innovation Lead', 'Data Scientist', 'Cybersecurity Analyst', 'Product Owner', 'R&D Manager'],  # Keeping typo for key matching
        'other': ['Decision Maker', 'Stakeholder', 'Operations Lead', 'Project Sponsor', 'Business Unit Head', 'Vendor Manager']
    }
    
    # Sector-based goals (from previous update)
    goal_options = {
        'medical': [
            f"Streamline patient data management and compliance using {product}.",
            f"Enhance telemedicine capabilities and remote monitoring with {product}.",
            f"Improve diagnostic accuracy and workflow efficiency via {product}.",
            f"Strengthen data security and regulatory reporting through {product}.",
            f"Optimize resource allocation and staff scheduling leveraging {product}."
        ],
        'retail': [
            f"Enhance inventory tracking and customer analytics with {product}.",
            f"Boost personalized marketing and sales forecasting using {product}.",
            f"Streamline supply chain and omnichannel experiences via {product}.",
            f"Improve loss prevention and fraud detection through {product}.",
            f"Accelerate checkout processes and loyalty program engagement leveraging {product}."
        ],
        'software': [
            f"Improve development workflows and scalability via {product}.",
            f"Enhance code collaboration and CI/CD pipeline automation using {product}.",
            f"Strengthen security testing and bug tracking with {product}.",
            f"Optimize cloud deployment and resource management through {product}.",
            f"Facilitate agile sprint planning and team productivity leveraging {product}."
        ],
        'services': [
            f"Optimize service delivery and client onboarding through {product}.",
            f"Enhance project management and resource allocation using {product}.",
            f"Improve billing accuracy and contract compliance with {product}.",
            f"Streamline customer support and feedback loops via {product}.",
            f"Boost consulting efficiency and knowledge sharing leveraging {product}."
        ],
        'entertainment': [
            f"Boost content production efficiency and audience engagement with {product}.",
            f"Enhance streaming quality and recommendation algorithms using {product}.",
            f"Streamline event ticketing and fan interaction via {product}.",
            f"Improve royalty tracking and rights management through {product}.",
            f"Optimize ad placement and monetization strategies leveraging {product}."
        ],
        'telecommunications': [
            f"Upgrade network monitoring and reliability using {product}.",
            f"Enhance 5G rollout and spectrum management with {product}.",
            f"Improve customer churn prediction and service personalization via {product}.",
            f"Streamline billing disputes and infrastructure maintenance through {product}.",
            f"Boost IoT device integration and data analytics leveraging {product}."
        ],
        'finance': [
            f"Strengthen fraud detection and reporting capabilities with {product}.",
            f"Enhance algorithmic trading and risk assessment using {product}.",
            f"Streamline compliance audits and transaction monitoring via {product}.",
            f"Improve portfolio optimization and client advisory through {product}.",
            f"Optimize payment processing and blockchain integration leveraging {product}."
        ],
        'employment': [
            f"Automate recruitment processes and talent pipeline management via {product}.",
            f"Enhance employee onboarding and performance tracking using {product}.",
            f"Streamline diversity hiring and skills gap analysis with {product}.",
            f"Improve payroll automation and benefits administration through {product}.",
            f"Boost internal mobility and career development programs leveraging {product}."
        ],
        'marketing': [
            f"Drive targeted campaigns and ROI measurement using {product}.",
            f"Enhance lead generation and A/B testing capabilities with {product}.",
            f"Streamline content creation and multi-channel distribution via {product}.",
            f"Improve customer segmentation and sentiment analysis through {product}.",
            f"Optimize SEO strategies and conversion funnel tracking leveraging {product}."
        ],
        'technolgy': [
            f"Accelerate innovation and system integration with {product}.",
            f"Enhance cybersecurity protocols and threat detection using {product}.",
            f"Streamline DevOps automation and hardware provisioning via {product}.",
            f"Improve data lake management and AI model deployment through {product}.",
            f"Boost edge computing and real-time analytics leveraging {product}."
        ],
        'other': [
            f"Achieve operational efficiency goals with {product} implementation.",
            f"Enhance cross-functional collaboration using {product}.",
            f"Streamline vendor management and procurement processes via {product}.",
            f"Improve sustainability tracking and ESG reporting through {product}.",
            f"Optimize budget forecasting and cost control leveraging {product}."
        ]
    }
    
    # Sector-based mid_activities (5-7 per sector)
    mid_activities_options = {
        'medical': [
            "Conducted product demo; positive feedback on HIPAA compliance features.",
            "Addressed regulatory concerns; shared case studies from healthcare peers.",
            "Follow-up email with customized ROI calculator; requested clinician input.",
            "Technical deep-dive on EHR integration; resolved data migration queries.",
            "Escalated to medical board for review; awaiting ethics approval.",
            "Shared pilot program proposal; aligned on implementation timeline.",
            "Conducted stakeholder workshop; gathered requirements for customization."
        ],
        'retail': [
            "Conducted product demo; positive feedback on real-time inventory sync.",
            "Addressed POS integration concerns; shared retail chain success stories.",
            "Follow-up email with dynamic pricing model; requested sales team alignment.",
            "Technical deep-dive on e-commerce API; resolved omnichannel sync issues.",
            "Escalated to merchandising team; awaiting seasonal rollout sign-off.",
            "Shared customer loyalty analytics report; highlighted engagement metrics.",
            "Conducted store visit simulation; gathered feedback on user interface."
        ],
        'software': [
            "Conducted product demo; positive feedback on API scalability.",
            "Addressed version control integration; shared dev team case studies.",
            "Follow-up email with code sample repo; requested architecture review.",
            "Technical deep-dive on cloud provisioning; resolved deployment queries.",
            "Escalated to engineering leads; awaiting sprint integration plan.",
            "Shared performance benchmarking data; aligned on load testing.",
            "Conducted pair-programming session; gathered agile workflow inputs."
        ],
        'services': [
            "Conducted product demo; positive feedback on workflow automation.",
            "Addressed SLA compliance concerns; shared service provider examples.",
            "Follow-up email with service blueprint; requested ops team alignment.",
            "Technical deep-dive on CRM sync; resolved client data queries.",
            "Escalated to delivery directors; awaiting contract amendment sign-off.",
            "Shared resource allocation dashboard; highlighted efficiency gains.",
            "Conducted process mapping workshop; gathered onboarding feedback."
        ],
        'entertainment': [
            "Conducted product demo; positive feedback on content metadata tagging.",
            "Addressed streaming latency concerns; shared media platform stories.",
            "Follow-up email with audience analytics mockup; requested creative input.",
            "Technical deep-dive on DRM integration; resolved rights management issues.",
            "Escalated to production heads; awaiting pilot episode rollout.",
            "Shared engagement heatmaps; aligned on recommendation algorithms.",
            "Conducted virtual screening session; gathered user experience feedback."
        ],
        'telecommunications': [
            "Conducted product demo; positive feedback on network diagnostics.",
            "Addressed spectrum allocation concerns; shared telco case studies.",
            "Follow-up email with bandwidth simulator; requested ops alignment.",
            "Technical deep-dive on 5G handoff; resolved latency queries.",
            "Escalated to network planners; awaiting infrastructure upgrade sign-off.",
            "Shared churn prediction models; highlighted retention strategies.",
            "Conducted site survey simulation; gathered IoT integration inputs."
        ],
        'finance': [
            "Conducted product demo; positive feedback on transaction auditing.",
            "Addressed KYC compliance concerns; shared banking peer examples.",
            "Follow-up email with risk scoring tool; requested compliance review.",
            "Technical deep-dive on blockchain ledger; resolved audit trail issues.",
            "Escalated to risk committees; awaiting regulatory nod.",
            "Shared fraud pattern analytics; aligned on alert thresholds.",
            "Conducted scenario planning workshop; gathered portfolio inputs."
        ],
        'employment': [
            "Conducted product demo; positive feedback on applicant tracking.",
            "Addressed DEI metrics concerns; shared HR tech stories.",
            "Follow-up email with talent pipeline dashboard; requested recruiter alignment.",
            "Technical deep-dive on skills matching; resolved onboarding queries.",
            "Escalated to talent leads; awaiting policy integration sign-off.",
            "Shared retention forecasting; highlighted engagement surveys.",
            "Conducted role-playing interviews; gathered feedback on automation."
        ],
        'marketing': [
            "Conducted product demo; positive feedback on campaign attribution.",
            "Addressed data privacy concerns; shared ad tech case studies.",
            "Follow-up email with A/B test planner; requested creative alignment.",
            "Technical deep-dive on pixel tracking; resolved conversion issues.",
            "Escalated to media buyers; awaiting budget allocation sign-off.",
            "Shared ROI projection models; aligned on KPI definitions.",
            "Conducted persona workshop; gathered segmentation inputs."
        ],
        'technolgy': [
            "Conducted product demo; positive feedback on edge processing.",
            "Addressed scalability concerns; shared tech firm examples.",
            "Follow-up email with prototype code; requested dev review.",
            "Technical deep-dive on API gateways; resolved security queries.",
            "Escalated to innovation boards; awaiting proof-of-concept sign-off.",
            "Shared latency benchmarks; aligned on throughput targets.",
            "Conducted hackathon session; gathered feature prioritization."
        ],
        'other': [
            "Conducted product demo; positive feedback on core functionalities.",
            "Addressed implementation concerns; shared cross-industry stories.",
            "Follow-up email with project charter; requested team alignment.",
            "Technical deep-dive on integrations; resolved compatibility issues.",
            "Escalated to decision-makers; awaiting strategic fit review.",
            "Shared benefit quantification; highlighted quick wins.",
            "Conducted gap analysis workshop; gathered customization needs."
        ]
    }
    
    # Sector-based outcome_reasons for Won (5-7 per sector)
    won_outcome_options = {
        'medical': [
            "Final negotiation successful; contract signed due to HIPAA alignment and cost savings.",
            "Budget approved; closed won after clinical trial validation and executive endorsement.",
            "Overcame regulatory hurdles; accelerated rollout sealed the deal with pilot success.",
            "Multi-year commitment secured; partnership expanded to include telemedicine modules.",
            "Key stakeholder buy-in achieved; ROI demo convinced the board on efficiency gains.",
            "Custom integration delivered ahead of schedule; won on superior support commitment.",
            "Competitive edge demonstrated; closed with exclusive vendor status."
        ],
        'retail': [
            "Final negotiation successful; contract signed due to omnichannel synergy and margins boost.",
            "Budget approved; closed won after seasonal pilot and merchandising team approval.",
            "Overcame supply chain objections; accelerated inventory sync sealed the deal.",
            "Multi-year commitment secured; partnership expanded to loyalty integrations.",
            "Key stakeholder buy-in achieved; analytics demo convinced ops on revenue uplift.",
            "Custom pricing model accepted; won on volume discount and quick deployment.",
            "Competitive analysis favored us; closed with preferred partner designation."
        ],
        'software': [
            "Final negotiation successful; contract signed due to seamless CI/CD fit and scalability.",
            "Budget approved; closed won after code review and dev team endorsement.",
            "Overcame integration concerns; accelerated API rollout sealed the deal.",
            "Multi-year commitment secured; partnership expanded to cloud migrations.",
            "Key stakeholder buy-in achieved; benchmark demo convinced on performance gains.",
            "Custom dev tools provided; won on open-source compatibility commitment.",
            "Competitive PoC won; closed with agile methodology alignment."
        ],
        'services': [
            "Final negotiation successful; contract signed due to SLA guarantees and onboarding ease.",
            "Budget approved; closed won after process audit and delivery team sign-off.",
            "Overcame billing objections; accelerated support tiers sealed the deal.",
            "Multi-year commitment secured; partnership expanded to consulting add-ons.",
            "Key stakeholder buy-in achieved; dashboard demo convinced on efficiency metrics.",
            "Custom service blueprints accepted; won on client success milestones.",
            "Competitive RFP response excelled; closed with framework agreement."
        ],
        'entertainment': [
            "Final negotiation successful; contract signed due to engagement metrics and content fit.",
            "Budget approved; closed won after screening pilot and creative endorsement.",
            "Overcame rights management issues; accelerated metadata tools sealed the deal.",
            "Multi-year commitment secured; partnership expanded to ad revenue shares.",
            "Key stakeholder buy-in achieved; algo demo convinced on audience growth.",
            "Custom fan interaction features; won on exclusive content integrations.",
            "Competitive pitch won; closed with co-production opportunities."
        ],
        'telecommunications': [
            "Final negotiation successful; contract signed due to reliability SLAs and 5G readiness.",
            "Budget approved; closed won after network sim and ops team approval.",
            "Overcame bandwidth concerns; accelerated IoT pilots sealed the deal.",
            "Multi-year commitment secured; partnership expanded to spectrum auctions.",
            "Key stakeholder buy-in achieved; churn model demo convinced on retention.",
            "Custom monitoring dashboards; won on proactive outage predictions.",
            "Competitive tender favored; closed with infrastructure consortium role."
        ],
        'finance': [
            "Final negotiation successful; contract signed due to compliance audits and fraud reduction.",
            "Budget approved; closed won after risk assessment and board endorsement.",
            "Overcame KYC hurdles; accelerated transaction processing sealed the deal.",
            "Multi-year commitment secured; partnership expanded to fintech APIs.",
            "Key stakeholder buy-in achieved; algo demo convinced on risk-adjusted returns.",
            "Custom reporting suites; won on regulatory filing automations.",
            "Competitive due diligence passed; closed with custodial services add-on."
        ],
        'employment': [
            "Final negotiation successful; contract signed due to ATS integrations and hiring speed.",
            "Budget approved; closed won after DEI audit and HR team sign-off.",
            "Overcame skills gap concerns; accelerated onboarding sealed the deal.",
            "Multi-year commitment secured; partnership expanded to L&D platforms.",
            "Key stakeholder buy-in achieved; pipeline demo convinced on talent ROI.",
            "Custom retention tools; won on predictive analytics commitments.",
            "Competitive vendor review won; closed with enterprise license."
        ],
        'marketing': [
            "Final negotiation successful; contract signed due to ROI tracking and campaign lift.",
            "Budget approved; closed won after A/B test results and creative approval.",
            "Overcame privacy objections; accelerated segmentation sealed the deal.",
            "Multi-year commitment secured; partnership expanded to influencer tools.",
            "Key stakeholder buy-in achieved; funnel demo convinced on conversions.",
            "Custom attribution models; won on multi-channel support.",
            "Competitive media pitch excelled; closed with retainer agreement."
        ],
        'technolgy': [
            "Final negotiation successful; contract signed due to edge computing fit and latency cuts.",
            "Budget approved; closed won after PoC validation and tech lead endorsement.",
            "Overcame cyber concerns; accelerated deployment sealed the deal.",
            "Multi-year commitment secured; partnership expanded to AI accelerators.",
            "Key stakeholder buy-in achieved; benchmark demo convinced on throughput.",
            "Custom hardware provisioning; won on R&D collaboration pledges.",
            "Competitive innovation challenge won; closed with joint lab setup."
        ],
        'other': [
            "Final negotiation successful; contract signed due to efficiency gains and quick ROI.",
            "Budget approved; closed won after gap analysis and ops endorsement.",
            "Overcame implementation hurdles; accelerated pilot sealed the deal.",
            "Multi-year commitment secured; partnership expanded to vendor ecosystem.",
            "Key stakeholder buy-in achieved; benefit demo convinced on KPIs.",
            "Custom workflows accepted; won on scalability assurances.",
            "Competitive evaluation favored; closed with framework contract."
        ]
    }
    
    # Sector-based outcome_reasons for Lost (5-7 per sector)
    lost_outcome_options = {
        'medical': [
            "Pricing objection unresolvable; lost to in-house solution with lower upfront costs.",
            "Internal delays due to ethics review; deal stalled and went cold.",
            "Shift in priorities to telehealth pivot; budget reallocated to competitors.",
            "Key clinician changed; new requirements mismatched our compliance features.",
            "Regulatory approval timeline exceeded; customer opted for quicker alternatives.",
            "Pilot feedback on usability negative; lost on integration complexities.",
            "Executive veto on vendor lock-in; deal abandoned post-audit."
        ],
        'retail': [
            "Pricing objection unresolvable; lost to open-source with no licensing fees.",
            "Internal delays from seasonal peaks; deal stalled and went cold.",
            "Shift in priorities to e-com focus; budget reallocated to POS upgrades.",
            "Key buyer changed; new demands mismatched our analytics depth.",
            "Omnichannel pilot failed sync test; customer opted for simpler tools.",
            "Merchandising veto on customization costs; deal abandoned post-demo.",
            "Competitor underbid on volume; lost on margin pressures."
        ],
        'software': [
            "Pricing objection unresolvable; lost to free tier competitors.",
            "Internal delays in sprint cycles; deal stalled and went cold.",
            "Shift in priorities to microservices; budget reallocated to AWS natives.",
            "Key dev lead changed; new stack mismatched our APIs.",
            "Code review flagged security gaps; customer opted for audited alternatives.",
            "Scalability PoC underperformed; lost on benchmark failures.",
            "Engineering veto on learning curve; deal abandoned post-hackathon."
        ],
        'services': [
            "Pricing objection unresolvable; lost to offshore providers with lower rates.",
            "Internal delays in contract reviews; deal stalled and went cold.",
            "Shift in priorities to digital transformation; budget reallocated to consultancies.",
            "Key ops manager changed; new SLAs mismatched our tiers.",
            "Onboarding pilot hit roadblocks; customer opted for plug-and-play options.",
            "Delivery veto on resource allocation; lost on scalability doubts.",
            "Competitor offered bundled services; deal abandoned post-RFP."
        ],
        'entertainment': [
            "Pricing objection unresolvable; lost to ad-supported free tiers.",
            "Internal delays from content calendars; deal stalled and went cold.",
            "Shift in priorities to VR focus; budget reallocated to niche tools.",
            "Key creative changed; new formats mismatched our metadata.",
            "Engagement pilot showed low lift; customer opted for legacy systems.",
            "Production veto on rights complexities; lost on integration issues.",
            "Competitor tied to major studio; deal abandoned post-pilot."
        ],
        'telecommunications': [
            "Pricing objection unresolvable; lost to incumbent vendors with legacy discounts.",
            "Internal delays in regulatory filings; deal stalled and went cold.",
            "Shift in priorities to fiber rollout; budget reallocated to hardware.",
            "Key network engineer changed; new specs mismatched our 5G.",
            "Churn model accuracy questioned; customer opted for proven analytics.",
            "Ops veto on downtime risks; lost on reliability concerns.",
            "Competitor bundled with spectrum; deal abandoned post-tender."
        ],
        'finance': [
            "Pricing objection unresolvable; lost to fintech startups with agile pricing.",
            "Internal delays in compliance checks; deal stalled and went cold.",
            "Shift in priorities to crypto regs; budget reallocated to blockchain natives.",
            "Key risk officer changed; new mandates mismatched our reporting.",
            "Fraud detection false positives high; customer opted for AI specialists.",
            "Board veto on data sovereignty; lost on audit trail gaps.",
            "Competitor certified by regulators; deal abandoned post-due diligence."
        ],
        'employment': [
            "Pricing objection unresolvable; lost to HR suites with free basics.",
            "Internal delays in policy updates; deal stalled and went cold.",
            "Shift in priorities to remote work; budget reallocated to comms tools.",
            "Key HR lead changed; new DEI focus mismatched our metrics.",
            "Talent pipeline pilot underdelivered; customer opted for manual processes.",
            "Recruitment veto on bias risks; lost on algorithm transparency.",
            "Competitor integrated with LinkedIn; deal abandoned post-trial."
        ],
        'marketing': [
            "Pricing objection unresolvable; lost to agency in-house tools.",
            "Internal delays from campaign cycles; deal stalled and went cold.",
            "Shift in priorities to social meta; budget reallocated to TikTok ads.",
            "Key strategist changed; new channels mismatched our attribution.",
            "A/B test ROI low; customer opted for Google Analytics free.",
            "Creative veto on privacy compliance; lost on cookie deprecation.",
            "Competitor offered white-label; deal abandoned post-pitch."
        ],
        'technolgy': [
            "Pricing objection unresolvable; lost to open hardware alternatives.",
            "Internal delays in R&D gates; deal stalled and went cold.",
            "Shift in priorities to quantum; budget reallocated to startups.",
            "Key innovator changed; new paradigms mismatched our edge.",
            "Throughput PoC failed benchmarks; customer opted for Nvidia stacks.",
            "Tech lead veto on power efficiency; lost on cooling requirements.",
            "Competitor open-sourced core; deal abandoned post-hackathon."
        ],
        'other': [
            "Pricing objection unresolvable; lost to cost-effective incumbents.",
            "Internal delays in approvals; deal stalled and went cold.",
            "Shift in priorities to core ops; budget reallocated elsewhere.",
            "Key decision-maker changed; new goals mismatched our value.",
            "Pilot showed limited uplift; customer opted for status quo.",
            "Stakeholder veto on risks; lost on unproven track record.",
            "Competitor had stronger references; deal abandoned post-review."
        ]
    }
    
    roles = role_options.get(sector, role_options['other'])
    goals = goal_options.get(sector, goal_options['other'])
    
    selected_role = random.choice(roles)
    customer_goal = random.choice(goals)
    
    # 3-5 activities
    num_activities = random.randint(3, 5)
    activity_dates = [engage + timedelta(days=(i * days // (num_activities + 1))) for i in range(num_activities)]
    
    notes = []
    notes.append(f"{activity_dates[0].strftime('%d-%m-%Y')}: Initial outreach by {sales_rep}. Meeting scheduled with {selected_role} ({account}). Discussed high-level customer's goal: {customer_goal}")
    
    mid_activities = mid_activities_options.get(sector, mid_activities_options['other'])
    for i in range(1, num_activities - 1):
        activity = random.choice(mid_activities)
        notes.append(f"{activity_dates[i].strftime('%d-%m-%Y')}: {activity}")
    
    # Outcome
    if stage == 'Won':
        outcome_reasons = won_outcome_options.get(sector, won_outcome_options['other'])
        notes.append(f"{activity_dates[-1].strftime('%d-%m-%Y')}: {random.choice(outcome_reasons)}")
    else:
        outcome_reasons = lost_outcome_options.get(sector, lost_outcome_options['other'])
        notes.append(f"{activity_dates[-1].strftime('%d-%m-%Y')}: {random.choice(outcome_reasons)}")
    
    return ' | '.join(notes)

df['Notes'] = df.apply(generate_notes, axis=1)

# Save updated CSV (Notes at end)
df.to_csv('Sales-Opportunity-Data-With-Notes.csv', index=False)
print("Updated CSV saved as 'Sales-Opportunity-Data-With-Notes.csv'")