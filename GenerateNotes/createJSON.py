import json
import pandas as pd

# Sector-based roles (expanded to 5-7 per sector)
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
    'technolgy': ['CTO', 'Systems Engineer', 'Innovation Lead', 'Data Scientist', 'Cybersecurity Analyst', 'Product Owner', 'R&D Manager'],
    'other': ['Decision Maker', 'Stakeholder', 'Operations Lead', 'Project Sponsor', 'Business Unit Head', 'Vendor Manager']
}

# Product-series specific goals, nested under sector
goal_options = {
    'medical': {
        'gtx': [
            "Leverage {product} (GTX series) for high-performance diagnostics and real-time imaging analysis.",
            "Enhance secure data visualization and AI-driven insights with {product} graphics capabilities.",
            "Optimize surgical planning simulations using {product}'s scalable computing power.",
            "Streamline telemedicine rendering and patient portal interactions via {product}.",
            "Improve compliance dashboards with {product}'s efficient data processing."
        ],
        'mg': [
            "Deploy {product} (MG series) to manage patient workflows and resource scheduling.",
            "Centralize analytics for outcomes tracking and predictive care modeling with {product}.",
            "Facilitate regulatory reporting and audit trails using {product}'s management tools.",
            "Enhance team collaboration on treatment plans via {product}.",
            "Automate inventory for medical supplies with {product}'s advanced tracking features."
        ],
        'gtk': [
            "Scale enterprise-wide health data platforms with {product} (GTK 500) for ultra-high throughput.",
            "Enable advanced genomic sequencing visualizations using {product}'s powerhouse specs.",
            "Integrate {product} for hospital-wide AI model training and deployment.",
            "Boost real-time monitoring systems with {product}'s enterprise-grade reliability.",
            "Transform research data handling with {product}'s massive parallel processing."
        ],
        'default': [
            "Streamline patient data management and compliance using {product}.",
            "Enhance telemedicine capabilities and remote monitoring with {product}.",
            "Improve diagnostic accuracy and workflow efficiency via {product}.",
            "Strengthen data security and regulatory reporting through {product}.",
            "Optimize resource allocation and staff scheduling leveraging {product}."
        ]
    },
    'retail': {
        'gtx': [
            "Power point-of-sale displays and dynamic pricing engines with {product} (GTX series).",
            "Enable high-res customer-facing kiosks and AR try-ons using {product}'s graphics.",
            "Scale e-commerce backend rendering for personalized recommendations via {product}.",
            "Optimize store analytics visualizations with {product}'s fast compute.",
            "Drive in-store digital signage with {product}'s reliable performance."
        ],
        'mg': [
            "Manage omnichannel inventory and supplier coordination using {product} (MG series).",
            "Track sales trends and demand forecasting with {product}'s analytics suite.",
            "Automate merchandising workflows and planogram updates via {product}.",
            "Centralize customer loyalty data management through {product}.",
            "Streamline returns processing and fraud alerts with {product}."
        ],
        'gtk': [
            "Handle massive retail data lakes and real-time analytics with {product} (GTK 500).",
            "Deploy {product} for supply chain simulations and predictive logistics.",
            "Empower enterprise CRM with {product}'s high-capacity processing.",
            "Integrate {product} for global store network monitoring.",
            "Accelerate big data queries on sales histories using {product}."
        ],
        'default': [
            "Enhance inventory tracking and customer analytics with {product}.",
            "Boost personalized marketing and sales forecasting using {product}.",
            "Streamline supply chain and omnichannel experiences via {product}.",
            "Improve loss prevention and fraud detection through {product}.",
            "Accelerate checkout processes and loyalty program engagement leveraging {product}."
        ]
    },
    'software': {
        'gtx': [
            "Accelerate GPU-accelerated builds and simulations with {product} (GTX series).",
            "Enhance 3D modeling and VR dev environments using {product}.",
            "Scale ML training pipelines via {product}'s parallel processing.",
            "Optimize game engine rendering with {product}.",
            "Boost CI/CD visualization dashboards through {product}."
        ],
        'mg': [
            "Orchestrate dev team workflows and issue tracking with {product} (MG series).",
            "Manage release cycles and dependency graphs using {product}.",
            "Automate code review processes via {product}.",
            "Centralize sprint planning and backlog grooming through {product}.",
            "Track security vulnerabilities with {product}'s monitoring tools."
        ],
        'gtk': [
            "Power enterprise-scale simulations with {product} (GTK 500).",
            "Deploy {product} for distributed computing clusters.",
            "Enable high-fidelity data viz in dev tools using {product}.",
            "Integrate {product} for AI-assisted coding at scale.",
            "Handle petabyte-scale repo management via {product}."
        ],
        'default': [
            "Improve development workflows and scalability via {product}.",
            "Enhance code collaboration and CI/CD pipeline automation using {product}.",
            "Strengthen security testing and bug tracking with {product}.",
            "Optimize cloud deployment and resource management through {product}.",
            "Facilitate agile sprint planning and team productivity leveraging {product}."
        ]
    },
    'services': {
        'gtx': [
            "Visualize client project timelines and Gantt charts with {product} (GTX series) for immersive reviews.",
            "Enhance virtual collaboration sessions using {product}'s high-res graphics rendering.",
            "Scale resource allocation simulations via {product}'s compute power.",
            "Optimize service blueprint visualizations with {product}.",
            "Drive interactive training modules through {product}."
        ],
        'mg': [
            "Coordinate client engagements and milestone tracking using {product} (MG series).",
            "Manage contract renewals and SLA monitoring with {product}.",
            "Automate feedback loops and satisfaction surveys via {product}.",
            "Centralize knowledge base for service delivery through {product}.",
            "Streamline billing cycles and invoice disputes with {product}."
        ],
        'gtk': [
            "Handle enterprise service desk operations with {product} (GTK 500) for high-volume ticketing.",
            "Deploy {product} for predictive maintenance in service fleets.",
            "Empower global team dashboards with {product}'s robust processing.",
            "Integrate {product} for cross-region compliance tracking.",
            "Accelerate analytics on service metrics using {product}."
        ],
        'default': [
            "Optimize service delivery and client onboarding through {product}.",
            "Enhance project management and resource allocation using {product}.",
            "Improve billing accuracy and contract compliance with {product}.",
            "Streamline customer support and feedback loops via {product}.",
            "Boost consulting efficiency and knowledge sharing leveraging {product}."
        ]
    },
    'entertainment': {
        'gtx': [
            "Render high-fidelity CGI scenes and VFX previews with {product} (GTX series).",
            "Enable real-time motion capture processing using {product}'s graphics acceleration.",
            "Scale audience analytics visualizations via {product}.",
            "Optimize streaming bitrate adaptation with {product}.",
            "Drive interactive fan experiences through {product}."
        ],
        'mg': [
            "Orchestrate content production schedules and asset libraries using {product} (MG series).",
            "Manage rights clearances and distribution rights with {product}.",
            "Automate subtitle synchronization and localization via {product}.",
            "Centralize talent booking and contract management through {product}.",
            "Track viewer engagement metrics with {product}."
        ],
        'gtk': [
            "Power massive content delivery networks with {product} (GTK 500).",
            "Deploy {product} for live event streaming at scale.",
            "Enable ultra-HD post-production pipelines using {product}.",
            "Integrate {product} for global distribution analytics.",
            "Handle petabyte-scale media archives via {product}."
        ],
        'default': [
            "Boost content production efficiency and audience engagement with {product}.",
            "Enhance streaming quality and recommendation algorithms using {product}.",
            "Streamline event ticketing and fan interaction via {product}.",
            "Improve royalty tracking and rights management through {product}.",
            "Optimize ad placement and monetization strategies leveraging {product}."
        ]
    },
    'telecommunications': {
        'gtx': [
            "Visualize network topologies and traffic flows with {product} (GTX series) for troubleshooting.",
            "Enhance spectrum analysis tools using {product}'s high-res rendering.",
            "Scale simulation of 5G beamforming via {product}.",
            "Optimize fault localization maps with {product}.",
            "Drive VR network training modules through {product}."
        ],
        'mg': [
            "Manage subscriber provisioning and billing cycles using {product} (MG series).",
            "Orchestrate tower maintenance schedules with {product}.",
            "Automate outage response workflows via {product}.",
            "Centralize customer care queues through {product}.",
            "Track network utilization trends with {product}."
        ],
        'gtk': [
            "Process terabit-scale traffic logs with {product} (GTK 500).",
            "Deploy {product} for predictive network capacity planning.",
            "Empower core router monitoring with {product}'s power.",
            "Integrate {product} for edge device orchestration.",
            "Accelerate anomaly detection queries using {product}."
        ],
        'default': [
            "Upgrade network monitoring and reliability using {product}.",
            "Enhance 5G rollout and spectrum management with {product}.",
            "Improve customer churn prediction and service personalization via {product}.",
            "Streamline billing disputes and infrastructure maintenance through {product}.",
            "Boost IoT device integration and data analytics leveraging {product}."
        ]
    },
    'finance': {
        'gtx': [
            "Render real-time market heatmaps and trading floors with {product} (GTX series).",
            "Enhance algorithmic visualization dashboards using {product}.",
            "Scale risk scenario simulations via {product}.",
            "Optimize portfolio performance graphs with {product}.",
            "Drive immersive compliance training through {product}."
        ],
        'mg': [
            "Manage transaction reconciliation and ledger balancing using {product} (MG series).",
            "Orchestrate compliance audits and reporting with {product}.",
            "Automate fraud alert workflows via {product}.",
            "Centralize client account management through {product}.",
            "Track investment performance metrics with {product}."
        ],
        'gtk': [
            "Handle high-frequency trading data streams with {product} (GTK 500).",
            "Deploy {product} for global market surveillance.",
            "Empower quantitative modeling with {product}'s capacity.",
            "Integrate {product} for blockchain transaction validation.",
            "Accelerate stress testing computations using {product}."
        ],
        'default': [
            "Strengthen fraud detection and reporting capabilities with {product}.",
            "Enhance algorithmic trading and risk assessment using {product}.",
            "Streamline compliance audits and transaction monitoring via {product}.",
            "Improve portfolio optimization and client advisory through {product}.",
            "Optimize payment processing and blockchain integration leveraging {product}."
        ]
    },
    'employment': {
        'gtx': [
            "Visualize organizational charts and talent maps with {product} (GTX series) for strategic planning.",
            "Enhance diversity analytics dashboards using {product}.",
            "Scale employee engagement simulations via {product}.",
            "Optimize career path visualizations with {product}.",
            "Drive VR onboarding experiences through {product}."
        ],
        'mg': [
            "Manage recruitment pipelines and candidate sourcing using {product} (MG series).",
            "Orchestrate performance review cycles with {product}.",
            "Automate benefits enrollment workflows via {product}.",
            "Centralize learning module tracking through {product}.",
            "Track turnover prediction models with {product}."
        ],
        'gtk': [
            "Process enterprise HR data warehouses with {product} (GTK 500).",
            "Deploy {product} for predictive hiring analytics.",
            "Empower global workforce planning with {product}.",
            "Integrate {product} for compliance reporting at scale.",
            "Accelerate skills inventory queries using {product}."
        ],
        'default': [
            "Automate recruitment processes and talent pipeline management via {product}.",
            "Enhance employee onboarding and performance tracking using {product}.",
            "Streamline diversity hiring and skills gap analysis with {product}.",
            "Improve payroll automation and benefits administration through {product}.",
            "Boost internal mobility and career development programs leveraging {product}."
        ]
    },
    'marketing': {
        'gtx': [
            "Render campaign performance heatmaps and A/B test visuals with {product} (GTX series).",
            "Enhance ad creative previews using {product}'s graphics.",
            "Scale audience journey simulations via {product}.",
            "Optimize content mockup rendering with {product}.",
            "Drive interactive brand experience demos through {product}."
        ],
        'mg': [
            "Manage multi-channel campaign orchestration using {product} (MG series).",
            "Track lead nurturing sequences with {product}.",
            "Automate personalization rule sets via {product}.",
            "Centralize asset libraries for content through {product}.",
            "Monitor sentiment analysis feeds with {product}."
        ],
        'gtk': [
            "Handle big data customer insights with {product} (GTK 500).",
            "Deploy {product} for real-time personalization engines.",
            "Empower global campaign analytics with {product}.",
            "Integrate {product} for cross-platform attribution.",
            "Accelerate predictive modeling on consumer behavior using {product}."
        ],
        'default': [
            "Drive targeted campaigns and ROI measurement using {product}.",
            "Enhance lead generation and A/B testing capabilities with {product}.",
            "Streamline content creation and multi-channel distribution via {product}.",
            "Improve customer segmentation and sentiment analysis through {product}.",
            "Optimize SEO strategies and conversion funnel tracking leveraging {product}."
        ]
    },
    'technolgy': {
        'gtx': [
            "Accelerate prototype rendering and CAD models with {product} (GTX series).",
            "Enhance IoT device simulations using {product}.",
            "Scale AR/VR testing environments via {product}.",
            "Optimize circuit board visualizations with {product}.",
            "Drive hardware debugging interfaces through {product}."
        ],
        'mg': [
            "Orchestrate R&D project pipelines using {product} (MG series).",
            "Manage patent tracking and IP portfolios with {product}.",
            "Automate testing suite deployments via {product}.",
            "Centralize innovation backlog through {product}.",
            "Track tech stack compatibility with {product}."
        ],
        'gtk': [
            "Power supercomputing clusters for tech research with {product} (GTK 500).",
            "Deploy {product} for quantum simulation frameworks.",
            "Enable high-throughput data processing using {product}.",
            "Integrate {product} for edge AI deployments.",
            "Handle exascale modeling via {product}."
        ],
        'default': [
            "Accelerate innovation and system integration with {product}.",
            "Enhance cybersecurity protocols and threat detection using {product}.",
            "Streamline DevOps automation and hardware provisioning via {product}.",
            "Improve data lake management and AI model deployment through {product}.",
            "Boost edge computing and real-time analytics leveraging {product}."
        ]
    },
    'other': {
        'gtx': [
            "Visualize operational dashboards and process flows with {product} (GTX series).",
            "Enhance simulation tools for business scenarios using {product}.",
            "Scale reporting graphics via {product}.",
            "Optimize workflow diagrams with {product}.",
            "Drive executive presentations through {product}."
        ],
        'mg': [
            "Manage cross-departmental projects using {product} (MG series).",
            "Orchestrate vendor collaborations with {product}.",
            "Automate routine approvals via {product}.",
            "Centralize document repositories through {product}.",
            "Track KPI progress with {product}."
        ],
        'gtk': [
            "Process enterprise-wide datasets with {product} (GTK 500).",
            "Deploy {product} for strategic forecasting models.",
            "Empower C-suite analytics with {product}.",
            "Integrate {product} for legacy system migrations.",
            "Accelerate decision support queries using {product}."
        ],
        'default': [
            "Achieve operational efficiency goals with {product} implementation.",
            "Enhance cross-functional collaboration using {product}.",
            "Streamline vendor management and procurement processes via {product}.",
            "Improve sustainability tracking and ESG reporting through {product}.",
            "Optimize budget forecasting and cost control leveraging {product}."
        ]
    }
}

# Product-series specific mid_activities, nested under sector
mid_activities_options = {
    'medical': {
        'gtx': [
            "Conducted {product} demo; highlighted GPU acceleration for medical imaging.",
            "Addressed rendering speed concerns; shared GTX case studies in diagnostics.",
            "Follow-up with {product} benchmark report; requested imaging team input.",
            "Technical deep-dive on {product} VR integration; resolved visualization queries.",
            "Escalated to radiology leads; awaiting high-res pilot sign-off.",
            "Shared {product} load balancing data; aligned on throughput needs.",
            "Conducted simulation workshop; gathered feedback on {product} scalability."
        ],
        'mg': [
            "Conducted {product} demo; focused on workflow automation for patient care.",
            "Addressed scheduling conflicts; shared MG management success stories.",
            "Follow-up email with {product} dashboard mockup; requested ops alignment.",
            "Technical deep-dive on {product} reporting; resolved compliance issues.",
            "Escalated to admin board; awaiting resource plan approval.",
            "Shared {product} analytics previews; highlighted efficiency metrics.",
            "Conducted process audit session; gathered customization for {product}."
        ],
        'gtk': [
            "Conducted {product} demo; emphasized enterprise-scale data handling.",
            "Addressed high-volume queries; shared GTK enterprise deployments.",
            "Follow-up with {product} capacity planning tool; requested IT review.",
            "Technical deep-dive on {product} clustering; resolved failover queries.",
            "Escalated to CIO; awaiting strategic infrastructure nod.",
            "Shared {product} performance audits; aligned on SLAs.",
            "Conducted scalability workshop; gathered inputs for {product} tuning."
        ],
        'default': [
            "Conducted product demo; positive feedback on HIPAA compliance features.",
            "Addressed regulatory concerns; shared case studies from healthcare peers.",
            "Follow-up email with customized ROI calculator; requested clinician input.",
            "Technical deep-dive on EHR integration; resolved data migration queries.",
            "Escalated to medical board for review; awaiting ethics approval.",
            "Shared pilot program proposal; aligned on implementation timeline.",
            "Conducted stakeholder workshop; gathered requirements for customization."
        ]
    },
    'retail': {
        'gtx': [
            "Conducted {product} demo; showcased AR fitting room simulations.",
            "Addressed display latency; shared GTX retail tech stories.",
            "Follow-up with {product} e-com rendering samples; requested UX input.",
            "Technical deep-dive on {product} kiosk integration; resolved API queries.",
            "Escalated to store ops; awaiting in-store pilot approval.",
            "Shared {product} traffic heatmap data; aligned on personalization.",
            "Conducted shopper journey workshop; gathered {product} feedback."
        ],
        'mg': [
            "Conducted {product} demo; focused on inventory orchestration.",
            "Addressed supplier sync issues; shared MG chain management cases.",
            "Follow-up email with {product} forecasting model; requested sales alignment.",
            "Technical deep-dive on {product} loyalty tracking; resolved data flow.",
            "Escalated to merch team; awaiting planogram sign-off.",
            "Shared {product} demand analytics; highlighted stockout reductions.",
            "Conducted returns process session; gathered {product} customizations."
        ],
        'gtk': [
            "Conducted {product} demo; emphasized big data retail insights.",
            "Addressed query speed; shared GTK logistics successes.",
            "Follow-up with {product} supply chain simulator; requested logistics review.",
            "Technical deep-dive on {product} CRM scaling; resolved volume queries.",
            "Escalated to global ops; awaiting network integration nod.",
            "Shared {product} sales history benchmarks; aligned on predictions.",
            "Conducted omnichannel workshop; gathered inputs for {product}."
        ],
        'default': [
            "Conducted product demo; positive feedback on real-time inventory sync.",
            "Addressed POS integration concerns; shared retail chain success stories.",
            "Follow-up email with dynamic pricing model; requested sales team alignment.",
            "Technical deep-dive on e-commerce API; resolved omnichannel sync issues.",
            "Escalated to merchandising team; awaiting seasonal rollout sign-off.",
            "Shared customer loyalty analytics report; highlighted engagement metrics.",
            "Conducted store visit simulation; gathered feedback on user interface."
        ]
    },
    'software': {
        'gtx': [
            "Conducted {product} demo; highlighted GPU builds for ML models.",
            "Addressed VR dev latency; shared GTX simulation cases.",
            "Follow-up with {product} parallel processing repo; requested arch review.",
            "Technical deep-dive on {product} engine rendering; resolved perf queries.",
            "Escalated to dev leads; awaiting VR pilot sign-off.",
            "Shared {product} CI/CD viz data; aligned on pipeline needs.",
            "Conducted game dev workshop; gathered {product} scalability feedback."
        ],
        'mg': [
            "Conducted {product} demo; focused on workflow orchestration.",
            "Addressed dependency issues; shared MG release stories.",
            "Follow-up email with {product} sprint planner; requested PM alignment.",
            "Technical deep-dive on {product} review automation; resolved tool queries.",
            "Escalated to QA team; awaiting backlog integration.",
            "Shared {product} vuln tracking previews; highlighted security metrics.",
            "Conducted agile session; gathered {product} customizations."
        ],
        'gtk': [
            "Conducted {product} demo; emphasized cluster simulations.",
            "Addressed distributed load; shared GTK cluster cases.",
            "Follow-up with {product} AI coding tool; requested eng review.",
            "Technical deep-dive on {product} repo scaling; resolved storage queries.",
            "Escalated to CTO; awaiting exascale nod.",
            "Shared {product} throughput audits; aligned on benchmarks.",
            "Conducted hackathon; gathered inputs for {product}."
        ],
        'default': [
            "Conducted product demo; positive feedback on API scalability.",
            "Addressed version control integration; shared dev team case studies.",
            "Follow-up email with code sample repo; requested architecture review.",
            "Technical deep-dive on cloud provisioning; resolved deployment queries.",
            "Escalated to engineering leads; awaiting sprint integration plan.",
            "Shared performance benchmarking data; aligned on load testing.",
            "Conducted pair-programming session; gathered agile workflow inputs."
        ]
    },
    'services': {
        'gtx': [
            "Conducted {product} demo; showcased immersive project reviews.",
            "Addressed collaboration latency; shared GTX service cases.",
            "Follow-up with {product} Gantt renderer; requested PM input.",
            "Technical deep-dive on {product} training VR; resolved immersion queries.",
            "Escalated to delivery leads; awaiting blueprint sign-off.",
            "Shared {product} resource viz data; aligned on allocation.",
            "Conducted client workshop; gathered {product} feedback."
        ],
        'mg': [
            "Conducted {product} demo; focused on engagement management.",
            "Addressed SLA sync; shared MG contract stories.",
            "Follow-up email with {product} feedback loop; requested ops alignment.",
            "Technical deep-dive on {product} billing automation; resolved cycle queries.",
            "Escalated to success team; awaiting milestone integration.",
            "Shared {product} satisfaction previews; highlighted NPS metrics.",
            "Conducted onboarding session; gathered {product} customizations."
        ],
        'gtk': [
            "Conducted {product} demo; emphasized ticketing scale.",
            "Addressed fleet volume; shared GTK maintenance cases.",
            "Follow-up with {product} predictive tool; requested service review.",
            "Technical deep-dive on {product} desk clustering; resolved queue queries.",
            "Escalated to global heads; awaiting compliance nod.",
            "Shared {product} metric audits; aligned on SLAs.",
            "Conducted process workshop; gathered inputs for {product}."
        ],
        'default': [
            "Conducted product demo; positive feedback on workflow automation.",
            "Addressed SLA compliance concerns; shared service provider examples.",
            "Follow-up email with service blueprint; requested ops team alignment.",
            "Technical deep-dive on CRM sync; resolved client data queries.",
            "Escalated to delivery directors; awaiting contract amendment sign-off.",
            "Shared resource allocation dashboard; highlighted efficiency gains.",
            "Conducted process mapping workshop; gathered onboarding feedback."
        ]
    },
    'entertainment': {
        'gtx': [
            "Conducted {product} demo; highlighted CGI rendering speed.",
            "Addressed VFX latency; shared GTX media cases.",
            "Follow-up with {product} motion capture samples; requested creative input.",
            "Technical deep-dive on {product} bitrate adaptation; resolved stream queries.",
            "Escalated to producers; awaiting fan pilot sign-off.",
            "Shared {product} engagement data; aligned on metrics.",
            "Conducted screening workshop; gathered {product} feedback."
        ],
        'mg': [
            "Conducted {product} demo; focused on production scheduling.",
            "Addressed rights clearance; shared MG distribution stories.",
            "Follow-up email with {product} asset library; requested talent alignment.",
            "Technical deep-dive on {product} localization; resolved subtitle queries.",
            "Escalated to content heads; awaiting booking integration.",
            "Shared {product} viewer previews; highlighted retention metrics.",
            "Conducted rights session; gathered {product} customizations."
        ],
        'gtk': [
            "Conducted {product} demo; emphasized CDN scale.",
            "Addressed live volume; shared GTK streaming cases.",
            "Follow-up with {product} post-prod tool; requested dist review.",
            "Technical deep-dive on {product} HD pipelines; resolved format queries.",
            "Escalated to execs; awaiting global nod.",
            "Shared {product} archive audits; aligned on storage.",
            "Conducted event workshop; gathered inputs for {product}."
        ],
        'default': [
            "Conducted product demo; positive feedback on content metadata tagging.",
            "Addressed streaming latency concerns; shared media platform stories.",
            "Follow-up email with audience analytics mockup; requested creative input.",
            "Technical deep-dive on DRM integration; resolved rights management issues.",
            "Escalated to production heads; awaiting pilot episode rollout.",
            "Shared engagement heatmaps; aligned on recommendation algorithms.",
            "Conducted virtual screening session; gathered user experience feedback."
        ]
    },
    'telecommunications': {
        'gtx': [
            "Conducted {product} demo; showcased network flow visualizations.",
            "Addressed topology latency; shared GTX telco cases.",
            "Follow-up with {product} beamforming sim; requested arch input.",
            "Technical deep-dive on {product} fault maps; resolved diagnostic queries.",
            "Escalated to planners; awaiting 5G pilot sign-off.",
            "Shared {product} traffic data; aligned on capacity.",
            "Conducted VR training workshop; gathered {product} feedback."
        ],
        'mg': [
            "Conducted {product} demo; focused on provisioning management.",
            "Addressed outage workflows; shared MG response stories.",
            "Follow-up email with {product} care queue; requested ops alignment.",
            "Technical deep-dive on {product} utilization tracking; resolved trend queries.",
            "Escalated to customer leads; awaiting SLA integration.",
            "Shared {product} churn previews; highlighted retention metrics.",
            "Conducted maintenance session; gathered {product} customizations."
        ],
        'gtk': [
            "Conducted {product} demo; emphasized traffic log processing.",
            "Addressed capacity volume; shared GTK planning cases.",
            "Follow-up with {product} anomaly tool; requested core review.",
            "Technical deep-dive on {product} router monitoring; resolved stream queries.",
            "Escalated to CIO; awaiting edge nod.",
            "Shared {product} detection audits; aligned on predictions.",
            "Conducted IoT workshop; gathered inputs for {product}."
        ],
        'default': [
            "Conducted product demo; positive feedback on network diagnostics.",
            "Addressed spectrum allocation concerns; shared telco case studies.",
            "Follow-up email with bandwidth simulator; requested ops alignment.",
            "Technical deep-dive on 5G handoff; resolved latency queries.",
            "Escalated to network planners; awaiting infrastructure upgrade sign-off.",
            "Shared churn prediction models; highlighted retention strategies.",
            "Conducted site survey simulation; gathered IoT integration inputs."
        ]
    },
    'finance': {
        'gtx': [
            "Conducted {product} demo; highlighted market heatmap rendering.",
            "Addressed trading latency; shared GTX finance cases.",
            "Follow-up with {product} scenario sim; requested risk input.",
            "Technical deep-dive on {product} portfolio graphs; resolved perf queries.",
            "Escalated to quants; awaiting training pilot sign-off.",
            "Shared {product} algo data; aligned on speed.",
            "Conducted compliance workshop; gathered {product} feedback."
        ],
        'mg': [
            "Conducted {product} demo; focused on ledger management.",
            "Addressed audit workflows; shared MG reporting stories.",
            "Follow-up email with {product} alert system; requested compliance alignment.",
            "Technical deep-dive on {product} reconciliation; resolved transaction queries.",
            "Escalated to treasury; awaiting fraud integration.",
            "Shared {product} performance previews; highlighted return metrics.",
            "Conducted filing session; gathered {product} customizations."
        ],
        'gtk': [
            "Conducted {product} demo; emphasized HFT streams.",
            "Addressed surveillance volume; shared GTK market cases.",
            "Follow-up with {product} modeling tool; requested quant review.",
            "Technical deep-dive on {product} validation; resolved chain queries.",
            "Escalated to board; awaiting stress nod.",
            "Shared {product} testing audits; aligned on computations.",
            "Conducted due diligence workshop; gathered inputs for {product}."
        ],
        'default': [
            "Conducted product demo; positive feedback on transaction auditing.",
            "Addressed KYC compliance concerns; shared banking peer examples.",
            "Follow-up email with risk scoring tool; requested compliance review.",
            "Technical deep-dive on blockchain ledger; resolved audit trail issues.",
            "Escalated to risk committees; awaiting regulatory nod.",
            "Shared fraud pattern analytics; aligned on alert thresholds.",
            "Conducted scenario planning workshop; gathered portfolio inputs."
        ]
    },
    'employment': {
        'gtx': [
            "Conducted {product} demo; showcased talent map visualizations.",
            "Addressed engagement latency; shared GTX HR cases.",
            "Follow-up with {product} path sim; requested L&D input.",
            "Technical deep-dive on {product} diversity graphs; resolved metric queries.",
            "Escalated to directors; awaiting onboarding pilot sign-off.",
            "Shared {product} survey data; aligned on retention.",
            "Conducted planning workshop; gathered {product} feedback."
        ],
        'mg': [
            "Conducted {product} demo; focused on pipeline management.",
            "Addressed review cycles; shared MG performance stories.",
            "Follow-up email with {product} enrollment tool; requested benefits alignment.",
            "Technical deep-dive on {product} module tracking; resolved learning queries.",
            "Escalated to acquisition; awaiting turnover integration.",
            "Shared {product} prediction previews; highlighted gap metrics.",
            "Conducted hiring session; gathered {product} customizations."
        ],
        'gtk': [
            "Conducted {product} demo; emphasized HR data warehouses.",
            "Addressed planning volume; shared GTK workforce cases.",
            "Follow-up with {product} analytics tool; requested global review.",
            "Technical deep-dive on {product} reporting; resolved compliance queries.",
            "Escalated to CHRO; awaiting inventory nod.",
            "Shared {product} skills audits; aligned on queries.",
            "Conducted mobility workshop; gathered inputs for {product}."
        ],
        'default': [
            "Conducted product demo; positive feedback on applicant tracking.",
            "Addressed DEI metrics concerns; shared HR tech stories.",
            "Follow-up email with talent pipeline dashboard; requested recruiter alignment.",
            "Technical deep-dive on skills matching; resolved onboarding queries.",
            "Escalated to talent leads; awaiting policy integration sign-off.",
            "Shared retention forecasting; highlighted engagement surveys.",
            "Conducted role-playing interviews; gathered feedback on automation."
        ]
    },
    'marketing': {
        'gtx': [
            "Conducted {product} demo; highlighted heatmap rendering.",
            "Addressed creative latency; shared GTX ad cases.",
            "Follow-up with {product} journey sim; requested strategist input.",
            "Technical deep-dive on {product} mockups; resolved conversion queries.",
            "Escalated to buyers; awaiting demo pilot sign-off.",
            "Shared {product} attribution data; aligned on ROI.",
            "Conducted brand workshop; gathered {product} feedback."
        ],
        'mg': [
            "Conducted {product} demo; focused on channel orchestration.",
            "Addressed nurturing issues; shared MG sequence stories.",
            "Follow-up email with {product} rule set; requested personalization alignment.",
            "Technical deep-dive on {product} asset library; resolved content queries.",
            "Escalated to creators; awaiting sentiment integration.",
            "Shared {product} analysis previews; highlighted segmentation metrics.",
            "Conducted campaign session; gathered {product} customizations."
        ],
        'gtk': [
            "Conducted {product} demo; emphasized insights scale.",
            "Addressed engine volume; shared GTK personalization cases.",
            "Follow-up with {product} attribution tool; requested platform review.",
            "Technical deep-dive on {product} modeling; resolved behavior queries.",
            "Escalated to CMO; awaiting predictive nod.",
            "Shared {product} consumer audits; aligned on models.",
            "Conducted funnel workshop; gathered inputs for {product}."
        ],
        'default': [
            "Conducted product demo; positive feedback on campaign attribution.",
            "Addressed data privacy concerns; shared ad tech case studies.",
            "Follow-up email with A/B test planner; requested creative alignment.",
            "Technical deep-dive on pixel tracking; resolved conversion issues.",
            "Escalated to media buyers; awaiting budget allocation sign-off.",
            "Shared ROI projection models; aligned on KPI definitions.",
            "Conducted persona workshop; gathered segmentation inputs."
        ]
    },
    'technolgy': {
        'gtx': [
            "Conducted {product} demo; showcased CAD acceleration.",
            "Addressed IoT latency; shared GTX prototype cases.",
            "Follow-up with {product} AR test samples; requested R&D input.",
            "Technical deep-dive on {product} board viz; resolved debug queries.",
            "Escalated to engineers; awaiting interface pilot sign-off.",
            "Shared {product} stack data; aligned on compatibility.",
            "Conducted innovation workshop; gathered {product} feedback."
        ],
        'mg': [
            "Conducted {product} demo; focused on project orchestration.",
            "Addressed IP tracking; shared MG patent stories.",
            "Follow-up email with {product} suite deploy; requested testing alignment.",
            "Technical deep-dive on {product} backlog; resolved innovation queries.",
            "Escalated to owners; awaiting vuln integration.",
            "Shared {product} compatibility previews; highlighted stack metrics.",
            "Conducted R&D session; gathered {product} customizations."
        ],
        'gtk': [
            "Conducted {product} demo; emphasized cluster power.",
            "Addressed sim volume; shared GTK quantum cases.",
            "Follow-up with {product} AI framework; requested edge review.",
            "Technical deep-dive on {product} deployments; resolved model queries.",
            "Escalated to CTO; awaiting exascale nod.",
            "Shared {product} throughput audits; aligned on handling.",
            "Conducted lab workshop; gathered inputs for {product}."
        ],
        'default': [
            "Conducted product demo; positive feedback on edge processing.",
            "Addressed scalability concerns; shared tech firm examples.",
            "Follow-up email with prototype code; requested dev review.",
            "Technical deep-dive on API gateways; resolved security queries.",
            "Escalated to innovation boards; awaiting proof-of-concept sign-off.",
            "Shared latency benchmarks; aligned on throughput targets.",
            "Conducted hackathon session; gathered feature prioritization."
        ]
    },
    'other': {
        'gtx': [
            "Conducted {product} demo; highlighted dashboard rendering.",
            "Addressed scenario latency; shared GTX ops cases.",
            "Follow-up with {product} flow sim; requested unit input.",
            "Technical deep-dive on {product} diagrams; resolved workflow queries.",
            "Escalated to heads; awaiting presentation pilot sign-off.",
            "Shared {product} KPI data; aligned on visuals.",
            "Conducted exec workshop; gathered {product} feedback."
        ],
        'mg': [
            "Conducted {product} demo; focused on project management.",
            "Addressed vendor sync; shared MG collab stories.",
            "Follow-up email with {product} approval tool; requested dept alignment.",
            "Technical deep-dive on {product} repos; resolved doc queries.",
            "Escalated to sponsors; awaiting routine integration.",
            "Shared {product} progress previews; highlighted KPI metrics.",
            "Conducted cross-function session; gathered {product} customizations."
        ],
        'gtk': [
            "Conducted {product} demo; emphasized dataset processing.",
            "Addressed forecast volume; shared GTK strategic cases.",
            "Follow-up with {product} model tool; requested C-suite review.",
            "Technical deep-dive on {product} migrations; resolved legacy queries.",
            "Escalated to board; awaiting support nod.",
            "Shared {product} decision audits; aligned on queries.",
            "Conducted planning workshop; gathered inputs for {product}."
        ],
        'default': [
            "Conducted product demo; positive feedback on core functionalities.",
            "Addressed implementation concerns; shared cross-industry stories.",
            "Follow-up email with project charter; requested team alignment.",
            "Technical deep-dive on integrations; resolved compatibility issues.",
            "Escalated to decision-makers; awaiting strategic fit review.",
            "Shared benefit quantification; highlighted quick wins.",
            "Conducted gap analysis workshop; gathered customization needs."
        ]
    }
}

# Product-series specific won_outcome_options, nested under sector
won_outcome_options = {
    'medical': {
        'gtx': [
            "Final negotiation successful; closed on {product}'s superior imaging speed and cost ROI.",
            "Budget approved; won after GTX pilot validated diagnostic accuracy gains.",
            "Overcame latency objections; {product} acceleration sealed with real-time demo.",
            "Multi-year deal; expanded to include {product} VR training modules.",
            "Stakeholder buy-in; {product} benchmarks convinced on throughput superiority.",
            "Custom tuning delivered; won on GTX-exclusive healthcare optimizations.",
            "Competitive edge in graphics; closed with bundled support package."
        ],
        'mg': [
            "Final negotiation successful; closed on {product}'s workflow automation ROI.",
            "Budget approved; won after MG pilot streamlined care coordination.",
            "Overcame scheduling objections; {product} analytics sealed with efficiency demo.",
            "Multi-year deal; expanded to include {product} predictive modeling.",
            "Stakeholder buy-in; {product} dashboards convinced on compliance gains.",
            "Custom reports delivered; won on MG-tailored regulatory tools.",
            "Competitive edge in management; closed with training package."
        ],
        'gtk': [
            "Final negotiation successful; closed on {product}'s enterprise throughput ROI.",
            "Budget approved; won after GTK deployment scaled health platforms.",
            "Overcame volume objections; {product} clustering sealed with reliability demo.",
            "Multi-year deal; expanded to include {product} AI integrations.",
            "Stakeholder buy-in; {product} audits convinced on SLAs.",
            "Custom capacity planning; won on GTK strategic fit.",
            "Competitive edge in scale; closed with migration support."
        ],
        'default': [
            "Final negotiation successful; contract signed due to HIPAA alignment and cost savings.",
            "Budget approved; closed won after clinical trial validation and executive endorsement.",
            "Overcame regulatory hurdles; accelerated rollout sealed the deal with pilot success.",
            "Multi-year commitment secured; partnership expanded to include telemedicine modules.",
            "Key stakeholder buy-in achieved; ROI demo convinced the board on efficiency gains.",
            "Custom integration delivered ahead of schedule; won on superior support commitment.",
            "Competitive edge demonstrated; closed with exclusive vendor status."
        ]
    },
    'retail': {
        'gtx': [
            "Final negotiation successful; closed on {product}'s AR engagement ROI.",
            "Budget approved; won after GTX kiosks boosted conversion rates.",
            "Overcame display objections; {product} rendering sealed with UX demo.",
            "Multi-year deal; expanded to include {product} signage networks.",
            "Stakeholder buy-in; {product} analytics convinced on personalization gains.",
            "Custom e-com tools; won on GTX omnichannel optimizations.",
            "Competitive edge in visuals; closed with deployment package."
        ],
        'mg': [
            "Final negotiation successful; closed on {product}'s inventory sync ROI.",
            "Budget approved; won after MG forecasting reduced stockouts.",
            "Overcame supplier objections; {product} tracking sealed with trend demo.",
            "Multi-year deal; expanded to include {product} loyalty systems.",
            "Stakeholder buy-in; {product} dashboards convinced on sales uplift.",
            "Custom merch tools; won on MG planogram fit.",
            "Competitive edge in management; closed with analytics support."
        ],
        'gtk': [
            "Final negotiation successful; closed on {product}'s logistics ROI.",
            "Budget approved; won after GTK simulations optimized supply chains.",
            "Overcame query objections; {product} CRM sealed with scale demo.",
            "Multi-year deal; expanded to include {product} global monitoring.",
            "Stakeholder buy-in; {product} benchmarks convinced on predictions.",
            "Custom data lakes; won on GTK enterprise capacity.",
            "Competitive edge in big data; closed with integration package."
        ],
        'default': [
            "Final negotiation successful; contract signed due to omnichannel synergy and margins boost.",
            "Budget approved; closed won after seasonal pilot and merchandising team approval.",
            "Overcame supply chain objections; accelerated inventory sync sealed the deal.",
            "Multi-year commitment secured; partnership expanded to loyalty integrations.",
            "Key stakeholder buy-in achieved; analytics demo convinced ops on revenue uplift.",
            "Custom pricing model accepted; won on volume discount and quick deployment.",
            "Competitive analysis favored us; closed with preferred partner designation."
        ]
    },
    'software': {
        'gtx': [
            "Final negotiation successful; closed on {product}'s GPU build acceleration ROI.",
            "Budget approved; won after GTX ML pipelines scaled training times.",
            "Overcame rendering objections; {product} VR dev sealed with immersive demo.",
            "Multi-year deal; expanded to include {product} game engine optimizations.",
            "Stakeholder buy-in; {product} benchmarks convinced on parallel gains.",
            "Custom shaders delivered; won on GTX-exclusive dev tools.",
            "Competitive edge in simulations; closed with SDK bundle."
        ],
        'mg': [
            "Final negotiation successful; closed on {product}'s workflow orchestration ROI.",
            "Budget approved; won after MG sprint tools boosted velocity.",
            "Overcame review objections; {product} automation sealed with efficiency demo.",
            "Multi-year deal; expanded to include {product} backlog integrations.",
            "Stakeholder buy-in; {product} dashboards convinced on vuln tracking.",
            "Custom CI/CD pipelines; won on MG agile fit.",
            "Competitive edge in collaboration; closed with training modules."
        ],
        'gtk': [
            "Final negotiation successful; closed on {product}'s cluster simulation ROI.",
            "Budget approved; won after GTK deployments handled petabyte repos.",
            "Overcame load objections; {product} AI coding sealed with scale demo.",
            "Multi-year deal; expanded to include {product} distributed clusters.",
            "Stakeholder buy-in; {product} audits convinced on throughput.",
            "Custom viz tools; won on GTK enterprise dev capacity.",
            "Competitive edge in high-fidelity; closed with migration support."
        ],
        'default': [
            "Final negotiation successful; contract signed due to seamless CI/CD fit and scalability.",
            "Budget approved; closed won after code review and dev team endorsement.",
            "Overcame integration concerns; accelerated API rollout sealed the deal.",
            "Multi-year commitment secured; partnership expanded to cloud migrations.",
            "Key stakeholder buy-in achieved; benchmark demo convinced on performance gains.",
            "Custom dev tools provided; won on open-source compatibility commitment.",
            "Competitive PoC won; closed with agile methodology alignment."
        ]
    },
    'services': {
        'gtx': [
            "Final negotiation successful; closed on {product}'s immersive review ROI.",
            "Budget approved; won after GTX Gantt charts enhanced collaboration.",
            "Overcame latency objections; {product} VR training sealed with engagement demo.",
            "Multi-year deal; expanded to include {product} blueprint visuals.",
            "Stakeholder buy-in; {product} benchmarks convinced on resource gains.",
            "Custom session tools; won on GTX service optimizations.",
            "Competitive edge in interactivity; closed with deployment package."
        ],
        'mg': [
            "Final negotiation successful; closed on {product}'s engagement management ROI.",
            "Budget approved; won after MG SLAs streamlined renewals.",
            "Overcame feedback objections; {product} loops sealed with NPS demo.",
            "Multi-year deal; expanded to include {product} knowledge bases.",
            "Stakeholder buy-in; {product} dashboards convinced on billing accuracy.",
            "Custom invoice tools; won on MG contract fit.",
            "Competitive edge in coordination; closed with support modules."
        ],
        'gtk': [
            "Final negotiation successful; closed on {product}'s ticketing scale ROI.",
            "Budget approved; won after GTK fleets predicted maintenance.",
            "Overcame queue objections; {product} desks sealed with volume demo.",
            "Multi-year deal; expanded to include {product} global compliance.",
            "Stakeholder buy-in; {product} audits convinced on metrics.",
            "Custom dashboards; won on GTK enterprise capacity.",
            "Competitive edge in high-volume; closed with integration support."
        ],
        'default': [
            "Final negotiation successful; contract signed due to SLA guarantees and onboarding ease.",
            "Budget approved; closed won after process audit and delivery team sign-off.",
            "Overcame billing objections; accelerated support tiers sealed the deal.",
            "Multi-year commitment secured; partnership expanded to consulting add-ons.",
            "Key stakeholder buy-in achieved; dashboard demo convinced on efficiency metrics.",
            "Custom service blueprints accepted; won on client success milestones.",
            "Competitive RFP response excelled; closed with framework agreement."
        ]
    },
    'entertainment': {
        'gtx': [
            "Final negotiation successful; closed on {product}'s CGI rendering ROI.",
            "Budget approved; won after GTX VFX previews accelerated production.",
            "Overcame bitrate objections; {product} adaptation sealed with stream demo.",
            "Multi-year deal; expanded to include {product} motion capture.",
            "Stakeholder buy-in; {product} benchmarks convinced on fidelity.",
            "Custom previews; won on GTX media optimizations.",
            "Competitive edge in real-time; closed with SDK bundle."
        ],
        'mg': [
            "Final negotiation successful; closed on {product}'s scheduling ROI.",
            "Budget approved; won after MG assets boosted content flow.",
            "Overcame clearance objections; {product} rights sealed with localization demo.",
            "Multi-year deal; expanded to include {product} talent bookings.",
            "Stakeholder buy-in; {product} dashboards convinced on engagement.",
            "Custom libraries; won on MG distribution fit.",
            "Competitive edge in orchestration; closed with analytics modules."
        ],
        'gtk': [
            "Final negotiation successful; closed on {product}'s CDN scale ROI.",
            "Budget approved; won after GTK streams handled live events.",
            "Overcame pipeline objections; {product} HD sealed with format demo.",
            "Multi-year deal; expanded to include {product} global archives.",
            "Stakeholder buy-in; {product} audits convinced on storage.",
            "Custom networks; won on GTK enterprise capacity.",
            "Competitive edge in ultra-HD; closed with migration support."
        ],
        'default': [
            "Final negotiation successful; contract signed due to engagement metrics and content fit.",
            "Budget approved; closed won after screening pilot and creative endorsement.",
            "Overcame rights management issues; accelerated metadata tools sealed the deal.",
            "Multi-year commitment secured; partnership expanded to ad revenue shares.",
            "Key stakeholder buy-in achieved; algo demo convinced on audience growth.",
            "Custom fan interaction features; won on exclusive content integrations.",
            "Competitive pitch won; closed with co-production opportunities."
        ]
    },
    'telecommunications': {
        'gtx': [
            "Final negotiation successful; closed on {product}'s topology viz ROI.",
            "Budget approved; won after GTX flows improved troubleshooting.",
            "Overcame handoff objections; {product} beamforming sealed with sim demo.",
            "Multi-year deal; expanded to include {product} fault maps.",
            "Stakeholder buy-in; {product} benchmarks convinced on diagnostics.",
            "Custom training; won on GTX telco optimizations.",
            "Competitive edge in visuals; closed with VR bundle."
        ],
        'mg': [
            "Final negotiation successful; closed on {product}'s provisioning ROI.",
            "Budget approved; won after MG responses reduced outages.",
            "Overcame utilization objections; {product} tracking sealed with trend demo.",
            "Multi-year deal; expanded to include {product} care queues.",
            "Stakeholder buy-in; {product} dashboards convinced on churn.",
            "Custom workflows; won on MG ops fit.",
            "Competitive edge in management; closed with retention modules."
        ],
        'gtk': [
            "Final negotiation successful; closed on {product}'s traffic ROI.",
            "Budget approved; won after GTK planning predicted capacity.",
            "Overcame anomaly objections; {product} monitoring sealed with scale demo.",
            "Multi-year deal; expanded to include {product} edge orchestration.",
            "Stakeholder buy-in; {product} audits convinced on predictions.",
            "Custom routers; won on GTK core capacity.",
            "Competitive edge in terabit; closed with integration support."
        ],
        'default': [
            "Final negotiation successful; contract signed due to reliability SLAs and 5G readiness.",
            "Budget approved; closed won after network sim and ops team approval.",
            "Overcame bandwidth concerns; accelerated IoT pilots sealed the deal.",
            "Multi-year commitment secured; partnership expanded to spectrum auctions.",
            "Key stakeholder buy-in achieved; churn model demo convinced on retention.",
            "Custom monitoring dashboards; won on proactive outage predictions.",
            "Competitive tender favored; closed with infrastructure consortium role."
        ]
    },
    'finance': {
        'gtx': [
            "Final negotiation successful; closed on {product}'s heatmap ROI.",
            "Budget approved; won after GTX dashboards enhanced trading.",
            "Overcame scenario objections; {product} graphs sealed with perf demo.",
            "Multi-year deal; expanded to include {product} compliance training.",
            "Stakeholder buy-in; {product} benchmarks convinced on speed.",
            "Custom algos; won on GTX finance optimizations.",
            "Competitive edge in real-time; closed with SDK bundle."
        ],
        'mg': [
            "Final negotiation successful; closed on {product}'s reconciliation ROI.",
            "Budget approved; won after MG audits streamlined reporting.",
            "Overcame alert objections; {product} fraud sealed with pattern demo.",
            "Multi-year deal; expanded to include {product} account management.",
            "Stakeholder buy-in; {product} dashboards convinced on performance.",
            "Custom ledgers; won on MG compliance fit.",
            "Competitive edge in orchestration; closed with filing modules."
        ],
        'gtk': [
            "Final negotiation successful; closed on {product}'s HFT ROI.",
            "Budget approved; won after GTK surveillance scaled markets.",
            "Overcame validation objections; {product} modeling sealed with quant demo.",
            "Multi-year deal; expanded to include {product} stress testing.",
            "Stakeholder buy-in; {product} audits convinced on computations.",
            "Custom streams; won on GTK enterprise capacity.",
            "Competitive edge in high-frequency; closed with migration support."
        ],
        'default': [
            "Final negotiation successful; contract signed due to compliance audits and fraud reduction.",
            "Budget approved; closed won after risk assessment and board endorsement.",
            "Overcame KYC hurdles; accelerated transaction processing sealed the deal.",
            "Multi-year commitment secured; partnership expanded to fintech APIs.",
            "Key stakeholder buy-in achieved; algo demo convinced on risk-adjusted returns.",
            "Custom reporting suites; won on regulatory filing automations.",
            "Competitive due diligence passed; closed with custodial services add-on."
        ]
    },
    'employment': {
        'gtx': [
            "Final negotiation successful; closed on {product}'s talent map ROI.",
            "Budget approved; won after GTX charts boosted planning.",
            "Overcame path objections; {product} diversity sealed with metric demo.",
            "Multi-year deal; expanded to include {product} onboarding VR.",
            "Stakeholder buy-in; {product} benchmarks convinced on engagement.",
            "Custom surveys; won on GTX HR optimizations.",
            "Competitive edge in visuals; closed with deployment package."
        ],
        'mg': [
            "Final negotiation successful; closed on {product}'s pipeline ROI.",
            "Budget approved; won after MG reviews enhanced performance.",
            "Overcame enrollment objections; {product} benefits sealed with workflow demo.",
            "Multi-year deal; expanded to include {product} learning tracking.",
            "Stakeholder buy-in; {product} dashboards convinced on turnover.",
            "Custom hiring; won on MG recruitment fit.",
            "Competitive edge in management; closed with prediction modules."
        ],
        'gtk': [
            "Final negotiation successful; closed on {product}'s HR scale ROI.",
            "Budget approved; won after GTK analytics predicted hiring.",
            "Overcame compliance objections; {product} reporting sealed with global demo.",
            "Multi-year deal; expanded to include {product} skills inventory.",
            "Stakeholder buy-in; {product} audits convinced on queries.",
            "Custom warehouses; won on GTK enterprise capacity.",
            "Competitive edge in data; closed with integration support."
        ],
        'default': [
            "Final negotiation successful; contract signed due to ATS integrations and hiring speed.",
            "Budget approved; closed won after DEI audit and HR team sign-off.",
            "Overcame skills gap concerns; accelerated onboarding sealed the deal.",
            "Multi-year commitment secured; partnership expanded to L&D platforms.",
            "Key stakeholder buy-in achieved; pipeline demo convinced on talent ROI.",
            "Custom retention tools; won on predictive analytics commitments.",
            "Competitive vendor review won; closed with enterprise license."
        ]
    },
    'marketing': {
        'gtx': [
            "Final negotiation successful; closed on {product}'s heatmap ROI.",
            "Budget approved; won after GTX mockups accelerated creatives.",
            "Overcame journey objections; {product} A/B sealed with conversion demo.",
            "Multi-year deal; expanded to include {product} brand experiences.",
            "Stakeholder buy-in; {product} benchmarks convinced on attribution.",
            "Custom funnels; won on GTX campaign optimizations.",
            "Competitive edge in interactivity; closed with SDK bundle."
        ],
        'mg': [
            "Final negotiation successful; closed on {product}'s orchestration ROI.",
            "Budget approved; won after MG sequences boosted nurturing.",
            "Overcame rule objections; {product} personalization sealed with segment demo.",
            "Multi-year deal; expanded to include {product} asset libraries.",
            "Stakeholder buy-in; {product} dashboards convinced on sentiment.",
            "Custom channels; won on MG multi-channel fit.",
            "Competitive edge in coordination; closed with analysis modules."
        ],
        'gtk': [
            "Final negotiation successful; closed on {product}'s insights ROI.",
            "Budget approved; won after GTK engines personalized real-time.",
            "Overcame modeling objections; {product} attribution sealed with platform demo.",
            "Multi-year deal; expanded to include {product} predictive behavior.",
            "Stakeholder buy-in; {product} audits convinced on consumers.",
            "Custom big data; won on GTK enterprise capacity.",
            "Competitive edge in scale; closed with migration support."
        ],
        'default': [
            "Final negotiation successful; contract signed due to ROI tracking and campaign lift.",
            "Budget approved; closed won after A/B test results and creative approval.",
            "Overcame privacy objections; accelerated segmentation sealed the deal.",
            "Multi-year commitment secured; partnership expanded to influencer tools.",
            "Key stakeholder buy-in achieved; funnel demo convinced on conversions.",
            "Custom attribution models; won on multi-channel support.",
            "Competitive media pitch excelled; closed with retainer agreement."
        ]
    },
    'technolgy': {
        'gtx': [
            "Final negotiation successful; closed on {product}'s CAD acceleration ROI.",
            "Budget approved; won after GTX prototypes enhanced IoT sims.",
            "Overcame AR objections; {product} testing sealed with R&D demo.",
            "Multi-year deal; expanded to include {product} board debugging.",
            "Stakeholder buy-in; {product} benchmarks convinced on compatibility.",
            "Custom interfaces; won on GTX innovation optimizations.",
            "Competitive edge in rendering; closed with SDK bundle."
        ],
        'mg': [
            "Final negotiation successful; closed on {product}'s pipeline ROI.",
            "Budget approved; won after MG patents streamlined IP.",
            "Overcame suite objections; {product} testing sealed with deployment demo.",
            "Multi-year deal; expanded to include {product} backlog innovation.",
            "Stakeholder buy-in; {product} dashboards convinced on stack.",
            "Custom R&D; won on MG project fit.",
            "Competitive edge in orchestration; closed with vuln modules."
        ],
        'gtk': [
            "Final negotiation successful; closed on {product}'s cluster ROI.",
            "Budget approved; won after GTK frameworks simulated quantum.",
            "Overcame deployment objections; {product} AI sealed with edge demo.",
            "Multi-year deal; expanded to include {product} exascale modeling.",
            "Stakeholder buy-in; {product} audits convinced on handling.",
            "Custom labs; won on GTK enterprise capacity.",
            "Competitive edge in supercomputing; closed with migration support."
        ],
        'default': [
            "Final negotiation successful; contract signed due to edge computing fit and latency cuts.",
            "Budget approved; closed won after PoC validation and tech lead endorsement.",
            "Overcame cyber concerns; accelerated deployment sealed the deal.",
            "Multi-year commitment secured; partnership expanded to AI accelerators.",
            "Key stakeholder buy-in achieved; benchmark demo convinced on throughput.",
            "Custom hardware provisioning; won on R&D collaboration pledges.",
            "Competitive innovation challenge won; closed with joint lab setup."
        ]
    },
    'other': {
        'gtx': [
            "Final negotiation successful; closed on {product}'s dashboard ROI.",
            "Budget approved; won after GTX flows optimized processes.",
            "Overcame sim objections; {product} visuals sealed with exec demo.",
            "Multi-year deal; expanded to include {product} workflow diagrams.",
            "Stakeholder buy-in; {product} benchmarks convinced on KPIs.",
            "Custom presentations; won on GTX ops optimizations.",
            "Competitive edge in interactivity; closed with deployment package."
        ],
        'mg': [
            "Final negotiation successful; closed on {product}'s management ROI.",
            "Budget approved; won after MG collaborations boosted vendors.",
            "Overcame approval objections; {product} routines sealed with dept demo.",
            "Multi-year deal; expanded to include {product} document repos.",
            "Stakeholder buy-in; {product} dashboards convinced on progress.",
            "Custom projects; won on MG cross-function fit.",
            "Competitive edge in coordination; closed with KPI modules."
        ],
        'gtk': [
            "Final negotiation successful; closed on {product}'s dataset ROI.",
            "Budget approved; won after GTK models forecasted strategy.",
            "Overcame migration objections; {product} legacy sealed with C-suite demo.",
            "Multi-year deal; expanded to include {product} decision support.",
            "Stakeholder buy-in; {product} audits convinced on queries.",
            "Custom planning; won on GTK enterprise capacity.",
            "Competitive edge in big data; closed with integration support."
        ],
        'default': [
            "Final negotiation successful; contract signed due to efficiency gains and quick ROI.",
            "Budget approved; closed won after gap analysis and ops endorsement.",
            "Overcame implementation hurdles; accelerated pilot sealed the deal.",
            "Multi-year commitment secured; partnership expanded to vendor ecosystem.",
            "Key stakeholder buy-in achieved; benefit demo convinced on KPIs.",
            "Custom workflows accepted; won on scalability assurances.",
            "Competitive evaluation favored; closed with framework contract."
        ]
    }
}

# Product-series specific lost_outcome_options, nested under sector
lost_outcome_options = {
    'medical': {
        'gtx': [
            "Pricing too high for GTX graphics; lost to budget-friendly CPU alternatives.",
            "Delays in imaging certs; deal cold due to {product} validation timeline.",
            "Priorities shifted to software-only; budget cut {product} hardware spend.",
            "New CTO favored open-source viz; mismatched {product}'s proprietary features.",
            "Pilot showed heat issues; opted for cooler competitors.",
            "{product} power draw vetoed; lost on energy efficiency concerns.",
            "Competitor undercut on bundle; abandoned post-GTX comparison."
        ],
        'mg': [
            "Pricing unresolvable for MG management; lost to basic spreadsheets.",
            "Delays in workflow certs; deal stalled on {product} rollout.",
            "Priorities to manual processes; budget reallocated from {product}.",
            "New PM favored legacy tools; mismatched {product}'s automation.",
            "Pilot usability low; opted for simpler alternatives.",
            "{product} integration vetoed; lost on custom needs.",
            "Competitor free tier; abandoned post-MG demo."
        ],
        'gtk': [
            "Pricing too high for GTK scale; lost to cloud-only options.",
            "Delays in cluster setup; deal cold on {product} deployment.",
            "Priorities to on-prem shift; budget cut {product} capacity.",
            "New IT head favored hybrid; mismatched {product}'s full power.",
            "Pilot volume underdelivered; opted for modular competitors.",
            "{product} failover concerns; lost on reliability.",
            "Competitor bundled infra; abandoned post-GTK audit."
        ],
        'default': [
            "Pricing objection unresolvable; lost to in-house solution with lower upfront costs.",
            "Internal delays due to ethics review; deal stalled and went cold.",
            "Shift in priorities to telehealth pivot; budget reallocated to competitors.",
            "Key clinician changed; new requirements mismatched our compliance features.",
            "Regulatory approval timeline exceeded; customer opted for quicker alternatives.",
            "Pilot feedback on usability negative; lost on integration complexities.",
            "Executive veto on vendor lock-in; deal abandoned post-audit."
        ]
    },
    'retail': {
        'gtx': [
            "Pricing too high for GTX displays; lost to basic LCD alternatives.",
            "Delays in AR certs; deal cold due to {product} UX validation.",
            "Priorities shifted to non-digital; budget cut {product} kiosk spend.",
            "New CEO favored in-store only; mismatched {product}'s e-com features.",
            "Pilot conversion low; opted for static signage competitors.",
            "{product} latency vetoed; lost on shopper flow concerns.",
            "Competitor undercut on visuals; abandoned post-GTX demo."
        ],
        'mg': [
            "Pricing unresolvable for MG inventory; lost to manual tracking.",
            "Delays in sync certs; deal stalled on {product} supplier rollout.",
            "Priorities to core stock; budget reallocated from {product}.",
            "New analyst favored spreadsheets; mismatched {product}'s forecasting.",
            "Pilot stockout high; opted for simpler tools.",
            "{product} trend integration vetoed; lost on data needs.",
            "Competitor free app; abandoned post-MG forecast."
        ],
        'gtk': [
            "Pricing too high for GTK data; lost to mid-tier analytics.",
            "Delays in lake setup; deal cold on {product} logistics deployment.",
            "Priorities to local ops; budget cut {product} global capacity.",
            "New ops head favored batch; mismatched {product}'s real-time.",
            "Pilot query slow; opted for lightweight competitors.",
            "{product} CRM scale concerns; lost on volume.",
            "Competitor bundled CRM; abandoned post-GTK sim."
        ],
        'default': [
            "Pricing objection unresolvable; lost to open-source with no licensing fees.",
            "Internal delays from seasonal peaks; deal stalled and went cold.",
            "Shift in priorities to e-com focus; budget reallocated to POS upgrades.",
            "Key buyer changed; new demands mismatched our analytics depth.",
            "Omnichannel pilot failed sync test; customer opted for simpler tools.",
            "Merchandising veto on customization costs; deal abandoned post-demo.",
            "Competitor underbid on volume; lost on margin pressures."
        ]
    },
    'software': {
        'gtx': [
            "Pricing too high for GTX builds; lost to CPU-only alternatives.",
            "Delays in GPU certs; deal cold due to {product} ML validation.",
            "Priorities shifted to CPU tasks; budget cut {product} parallel spend.",
            "New CTO favored standard libs; mismatched {product}'s VR features.",
            "Pilot training slow; opted for cloud GPU competitors.",
            "{product} shading vetoed; lost on dev curve concerns.",
            "Competitor undercut on SDK; abandoned post-GTX PoC."
        ],
        'mg': [
            "Pricing unresolvable for MG workflows; lost to Jira basics.",
            "Delays in review certs; deal stalled on {product} automation rollout.",
            "Priorities to solo tools; budget reallocated from {product}.",
            "New PM favored Trello; mismatched {product}'s sprint features.",
            "Pilot velocity low; opted for lightweight alternatives.",
            "{product} backlog integration vetoed; lost on custom needs.",
            "Competitor free tier; abandoned post-MG demo."
        ],
        'gtk': [
            "Pricing too high for GTK clusters; lost to single-node options.",
            "Delays in sim setup; deal cold on {product} deployment.",
            "Priorities to local dev; budget cut {product} petabyte capacity.",
            "New arch favored mono; mismatched {product}'s distributed power.",
            "Pilot repo overloaded; opted for git-only competitors.",
            "{product} viz concerns; lost on fidelity.",
            "Competitor open cluster; abandoned post-GTK audit."
        ],
        'default': [
            "Pricing objection unresolvable; lost to free tier competitors.",
            "Internal delays in sprint cycles; deal stalled and went cold.",
            "Shift in priorities to microservices; budget reallocated to AWS natives.",
            "Key dev lead changed; new stack mismatched our APIs.",
            "Code review flagged security gaps; customer opted for audited alternatives.",
            "Scalability PoC underperformed; lost on benchmark failures.",
            "Engineering veto on learning curve; deal abandoned post-hackathon."
        ]
    },
    'services': {
        'gtx': [
            "Pricing too high for GTX reviews; lost to 2D chart alternatives.",
            "Delays in VR certs; deal cold due to {product} collaboration validation.",
            "Priorities shifted to email; budget cut {product} immersive spend.",
            "New exec favored slides; mismatched {product}'s Gantt features.",
            "Pilot engagement low; opted for basic tools competitors.",
            "{product} latency vetoed; lost on team flow concerns.",
            "Competitor undercut on visuals; abandoned post-GTX demo."
        ],
        'mg': [
            "Pricing unresolvable for MG engagements; lost to calendar apps.",
            "Delays in SLA certs; deal stalled on {product} renewal rollout.",
            "Priorities to manual billing; budget reallocated from {product}.",
            "New manager favored Excel; mismatched {product}'s feedback features.",
            "Pilot NPS low; opted for survey-only alternatives.",
            "{product} loop integration vetoed; lost on custom needs.",
            "Competitor free CRM; abandoned post-MG demo."
        ],
        'gtk': [
            "Pricing too high for GTK desks; lost to small-ticket options.",
            "Delays in fleet setup; deal cold on {product} maintenance deployment.",
            "Priorities to local support; budget cut {product} global capacity.",
            "New director favored phone; mismatched {product}'s predictive power.",
            "Pilot queue overflow; opted for call-center competitors.",
            "{product} compliance concerns; lost on scale.",
            "Competitor bundled desk; abandoned post-GTK audit."
        ],
        'default': [
            "Pricing objection unresolvable; lost to offshore providers with lower rates.",
            "Internal delays in contract reviews; deal stalled and went cold.",
            "Shift in priorities to digital transformation; budget reallocated to consultancies.",
            "Key ops manager changed; new SLAs mismatched our tiers.",
            "Onboarding pilot hit roadblocks; customer opted for plug-and-play options.",
            "Delivery veto on resource allocation; lost on scalability doubts.",
            "Competitor offered bundled services; deal abandoned post-RFP."
        ]
    },
    'entertainment': {
        'gtx': [
            "Pricing too high for GTX CGI; lost to software-only renderers.",
            "Delays in VFX certs; deal cold due to {product} production timeline.",
            "Priorities shifted to story; budget cut {product} graphics spend.",
            "New director favored practical; mismatched {product}'s motion features.",
            "Pilot fidelity low; opted for mid-range competitors.",
            "{product} bitrate vetoed; lost on stream concerns.",
            "Competitor undercut on previews; abandoned post-GTX demo."
        ],
        'mg': [
            "Pricing unresolvable for MG scheduling; lost to whiteboards.",
            "Delays in rights certs; deal stalled on {product} clearance rollout.",
            "Priorities to indie; budget reallocated from {product}.",
            "New strategist favored email; mismatched {product}'s asset features.",
            "Pilot flow disrupted; opted for simple alternatives.",
            "{product} localization vetoed; lost on custom needs.",
            "Competitor free library; abandoned post-MG demo."
        ],
        'gtk': [
            "Pricing too high for GTK CDNs; lost to edge caches.",
            "Delays in stream setup; deal cold on {product} event deployment.",
            "Priorities to local; budget cut {product} global capacity.",
            "New exec favored YouTube; mismatched {product}'s HD power.",
            "Pilot bandwidth overflow; opted for streaming competitors.",
            "{product} format concerns; lost on pipelines.",
            "Competitor bundled archive; abandoned post-GTK audit."
        ],
        'default': [
            "Pricing objection unresolvable; lost to ad-supported free tiers.",
            "Internal delays from content calendars; deal stalled and went cold.",
            "Shift in priorities to VR focus; budget reallocated to niche tools.",
            "Key creative changed; new formats mismatched our metadata.",
            "Engagement pilot showed low lift; customer opted for legacy systems.",
            "Production veto on rights complexities; lost on integration issues.",
            "Competitor tied to major studio; deal abandoned post-pilot."
        ]
    },
    'telecommunications': {
        'gtx': [
            "Pricing too high for GTX topologies; lost to text-based maps.",
            "Delays in viz certs; deal cold due to {product} troubleshooting timeline.",
            "Priorities shifted to voice; budget cut {product} flow spend.",
            "New architect favored CLI; mismatched {product}'s beam features.",
            "Pilot diagnostic low; opted for console competitors.",
            "{product} handoff vetoed; lost on sim concerns.",
            "Competitor undercut on visuals; abandoned post-GTX demo."
        ],
        'mg': [
            "Pricing unresolvable for MG provisioning; lost to spreadsheets.",
            "Delays in response certs; deal stalled on {product} outage rollout.",
            "Priorities to field; budget reallocated from {product}.",
            "New lead favored manual; mismatched {product}'s queue features.",
            "Pilot response slow; opted for basic alternatives.",
            "{product} utilization vetoed; lost on trend needs.",
            "Competitor free tool; abandoned post-MG demo."
        ],
        'gtk': [
            "Pricing too high for GTK traffic; lost to sample logs.",
            "Delays in planning setup; deal cold on {product} capacity deployment.",
            "Priorities to legacy; budget cut {product} terabit capacity.",
            "New head favored dial-up; mismatched {product}'s anomaly power.",
            "Pilot detection low; opted for rule-based competitors.",
            "{product} monitoring concerns; lost on scale.",
            "Competitor bundled core; abandoned post-GTK audit."
        ],
        'default': [
            "Pricing objection unresolvable; lost to incumbent vendors with legacy discounts.",
            "Internal delays in regulatory filings; deal stalled and went cold.",
            "Shift in priorities to fiber rollout; budget reallocated to hardware.",
            "Key network engineer changed; new specs mismatched our 5G.",
            "Churn model accuracy questioned; customer opted for proven analytics.",
            "Ops veto on downtime risks; lost on reliability concerns.",
            "Competitor bundled with spectrum; deal abandoned post-tender."
        ]
    },
    'finance': {
        'gtx': [
            "Pricing too high for GTX heatmaps; lost to line charts.",
            "Delays in trading certs; deal cold due to {product} dashboard timeline.",
            "Priorities shifted to reports; budget cut {product} viz spend.",
            "New CFO favored tables; mismatched {product}'s scenario features.",
            "Pilot speed low; opted for Excel competitors.",
            "{product} graph vetoed; lost on perf concerns.",
            "Competitor undercut on algos; abandoned post-GTX demo."
        ],
        'mg': [
            "Pricing unresolvable for MG reconciliation; lost to ledgers.",
            "Delays in audit certs; deal stalled on {product} reporting rollout.",
            "Priorities to cash; budget reallocated from {product}.",
            "New analyst favored manual; mismatched {product}'s alert features.",
            "Pilot pattern miss; opted for rule-based alternatives.",
            "{product} fraud vetoed; lost on custom needs.",
            "Competitor free audit; abandoned post-MG demo."
        ],
        'gtk': [
            "Pricing too high for GTK HFT; lost to batch processing.",
            "Delays in surveillance setup; deal cold on {product} market deployment.",
            "Priorities to quarterly; budget cut {product} stream capacity.",
            "New director favored spreadsheets; mismatched {product}'s modeling power.",
            "Pilot quant low; opted for mid-tier competitors.",
            "{product} validation concerns; lost on chain.",
            "Competitor bundled quant; abandoned post-GTK audit."
        ],
        'default': [
            "Pricing objection unresolvable; lost to fintech startups with agile pricing.",
            "Internal delays in compliance checks; deal stalled and went cold.",
            "Shift in priorities to crypto regs; budget reallocated to blockchain natives.",
            "Key risk officer changed; new mandates mismatched our reporting.",
            "Fraud detection false positives high; customer opted for AI specialists.",
            "Board veto on data sovereignty; lost on audit trail gaps.",
            "Competitor certified by regulators; deal abandoned post-due diligence."
        ]
    },
    'employment': {
        'gtx': [
            "Pricing too high for GTX maps; lost to org charts.",
            "Delays in planning certs; deal cold due to {product} talent timeline.",
            "Priorities shifted to resumes; budget cut {product} viz spend.",
            "New director favored lists; mismatched {product}'s diversity features.",
            "Pilot engagement low; opted for survey competitors.",
            "{product} path vetoed; lost on metric concerns.",
            "Competitor undercut on surveys; abandoned post-GTX demo."
        ],
        'mg': [
            "Pricing unresolvable for MG pipelines; lost to job boards.",
            "Delays in review certs; deal stalled on {product} performance rollout.",
            "Priorities to interviews; budget reallocated from {product}.",
            "New lead favored calendars; mismatched {product}'s enrollment features.",
            "Pilot gap high; opted for manual alternatives.",
            "{product} benefits vetoed; lost on workflow needs.",
            "Competitor free HR; abandoned post-MG demo."
        ],
        'gtk': [
            "Pricing too high for GTK HR; lost to small data tools.",
            "Delays in analytics setup; deal cold on {product} hiring deployment.",
            "Priorities to local; budget cut {product} global capacity.",
            "New officer favored paper; mismatched {product}'s predictive power.",
            "Pilot inventory low; opted for spreadsheet competitors.",
            "{product} reporting concerns; lost on compliance.",
            "Competitor bundled skills; abandoned post-GTK audit."
        ],
        'default': [
            "Pricing objection unresolvable; lost to HR suites with free basics.",
            "Internal delays in policy updates; deal stalled and went cold.",
            "Shift in priorities to remote work; budget reallocated to comms tools.",
            "Key HR lead changed; new DEI focus mismatched our metrics.",
            "Talent pipeline pilot underdelivered; customer opted for manual processes.",
            "Recruitment veto on bias risks; lost on algorithm transparency.",
            "Competitor integrated with LinkedIn; deal abandoned post-trial."
        ]
    },
    'marketing': {
        'gtx': [
            "Pricing too high for GTX heatmaps; lost to bar graphs.",
            "Delays in creative certs; deal cold due to {product} mockup timeline.",
            "Priorities shifted to text; budget cut {product} viz spend.",
            "New CMO favored emails; mismatched {product}'s journey features.",
            "Pilot conversion low; opted for static competitors.",
            "{product} A/B vetoed; lost on funnel concerns.",
            "Competitor undercut on attribution; abandoned post-GTX demo."
        ],
        'mg': [
            "Pricing unresolvable for MG orchestration; lost to single-channel.",
            "Delays in sequence certs; deal stalled on {product} nurturing rollout.",
            "Priorities to social; budget reallocated from {product}.",
            "New strategist favored manual; mismatched {product}'s rule features.",
            "Pilot segment miss; opted for list-based alternatives.",
            "{product} personalization vetoed; lost on asset needs.",
            "Competitor free tool; abandoned post-MG demo."
        ],
        'gtk': [
            "Pricing too high for GTK insights; lost to sample data.",
            "Delays in engine setup; deal cold on {product} personalization deployment.",
            "Priorities to local; budget cut {product} big data capacity.",
            "New director favored Google; mismatched {product}'s modeling power.",
            "Pilot behavior low; opted for mid-tier competitors.",
            "{product} attribution concerns; lost on platform.",
            "Competitor bundled insights; abandoned post-GTK audit."
        ],
        'default': [
            "Pricing objection unresolvable; lost to agency in-house tools.",
            "Internal delays from campaign cycles; deal stalled and went cold.",
            "Shift in priorities to social meta; budget reallocated to TikTok ads.",
            "Key strategist changed; new channels mismatched our attribution.",
            "A/B test ROI low; customer opted for Google Analytics free.",
            "Creative veto on privacy compliance; lost on cookie deprecation.",
            "Competitor offered white-label; deal abandoned post-pitch."
        ]
    },
    'technolgy': {
        'gtx': [
            "Pricing too high for GTX CAD; lost to 2D drafters.",
            "Delays in prototype certs; deal cold due to {product} IoT timeline.",
            "Priorities shifted to code; budget cut {product} sim spend.",
            "New CTO favored text; mismatched {product}'s AR features.",
            "Pilot debug low; opted for console competitors.",
            "{product} board vetoed; lost on interface concerns.",
            "Competitor undercut on stack; abandoned post-GTX demo."
        ],
        'mg': [
            "Pricing unresolvable for MG pipelines; lost to notebooks.",
            "Delays in IP certs; deal stalled on {product} patent rollout.",
            "Priorities to prototypes; budget reallocated from {product}.",
            "New owner favored solo; mismatched {product}'s suite features.",
            "Pilot backlog high; opted for simple alternatives.",
            "{product} testing vetoed; lost on deploy needs.",
            "Competitor free backlog; abandoned post-MG demo."
        ],
        'gtk': [
            "Pricing too high for GTK clusters; lost to single machines.",
            "Delays in framework setup; deal cold on {product} quantum deployment.",
            "Priorities to lab; budget cut {product} exascale capacity.",
            "New manager favored desktop; mismatched {product}'s AI power.",
            "Pilot model low; opted for cloud competitors.",
            "{product} edge concerns; lost on deployments.",
            "Competitor open lab; abandoned post-GTK audit."
        ],
        'default': [
            "Pricing objection unresolvable; lost to open hardware alternatives.",
            "Internal delays in R&D gates; deal stalled and went cold.",
            "Shift in priorities to quantum; budget reallocated to startups.",
            "Key innovator changed; new paradigms mismatched our edge.",
            "Throughput PoC failed benchmarks; customer opted for Nvidia stacks.",
            "Tech lead veto on power efficiency; lost on cooling requirements.",
            "Competitor open-sourced core; deal abandoned post-hackathon."
        ]
    },
    'other': {
        'gtx': [
            "Pricing too high for GTX dashboards; lost to tables.",
            "Delays in flow certs; deal cold due to {product} ops timeline.",
            "Priorities shifted to reports; budget cut {product} viz spend.",
            "New head favored print; mismatched {product}'s sim features.",
            "Pilot KPI low; opted for basic competitors.",
            "{product} diagram vetoed; lost on workflow concerns.",
            "Competitor undercut on visuals; abandoned post-GTX demo."
        ],
        'mg': [
            "Pricing unresolvable for MG projects; lost to emails.",
            "Delays in collab certs; deal stalled on {product} vendor rollout.",
            "Priorities to solo; budget reallocated from {product}.",
            "New sponsor favored notes; mismatched {product}'s approval features.",
            "Pilot progress slow; opted for list alternatives.",
            "{product} routine vetoed; lost on doc needs.",
            "Competitor free manager; abandoned post-MG demo."
        ],
        'gtk': [
            "Pricing too high for GTK datasets; lost to samples.",
            "Delays in model setup; deal cold on {product} strategy deployment.",
            "Priorities to quarterly; budget cut {product} query capacity.",
            "New unit favored manual; mismatched {product}'s legacy power.",
            "Pilot decision low; opted for mid-tier competitors.",
            "{product} migration concerns; lost on support.",
            "Competitor bundled planning; abandoned post-GTK audit."
        ],
        'default': [
            "Pricing objection unresolvable; lost to cost-effective incumbents.",
            "Internal delays in approvals; deal stalled and went cold.",
            "Shift in priorities to core ops; budget reallocated elsewhere.",
            "Key decision-maker changed; new goals mismatched our value.",
            "Pilot showed limited uplift; customer opted for status quo.",
            "Stakeholder veto on risks; lost on unproven track record.",
            "Competitor had stronger references; deal abandoned post-review."
        ]
    }
}

configs = {
    'roles': role_options,
    'goals': goal_options,
    'mid_activities': mid_activities_options,
    'won_outcomes': won_outcome_options,
    'lost_outcomes': lost_outcome_options
}

for name, data in configs.items():
    with open(f'{name}.json', 'w') as f:
        json.dump(data, f, indent=4)

print("JSON config files generated!")