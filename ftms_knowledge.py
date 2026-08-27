""" 
FTMS FleetPro Knowledge Base

What is FTMS Fleet Pro Application. What are its key highlights. 
How it is different from other applications.
Key Features...
Specialities....
FAQ?
Competitors
Business Benefits?
Version: 1.0
Author: Thankappan Dharmanathan
Why it is important """

FTMS_KNOWLEDGE = {
        "APPLICATION": {"keywords": ["ftms", "fleetpro","what is ftms", "about ftms", "application", "introduce ftms"],
                        
                        "answer":
                            
                        "FTMS FleetPro is an intelligent Fleet \nTransportation Management System that helps\n"
                        "businesses manage vehicles, drivers,\n maintenance, and operations from one platform.\n"
                        "It provides real-time insights, smart alerts\n, and decision support to improve efficiency\n" 
                        "reduce costs, and keep fleets running smoothly."},
        
           "FEATURES":{"keywords": ["feature","features", "key features", "main features", "capabilities", "what can it do",
                                 "functions", "what does it do", "options", "facitlities", "services", "tools",
                                 "system features", "ftms features","list features", "tell me the features"],
                    "answer":
                        
                        "FTMS FleetPro – Key Features:\n"
                        "🚚 Vehicle Management."
                        "👨‍✈️ Driver Management."
                        "🛠️ Maintenance Tracking."
                        "⛽ Fuel Monitoring."
                        "📅 Expiry & Service Alerts"
                        "📊 Smart Dashboard & Reports."
                       " 📄 PDF & Excel Export"
                        "🤖 AI Decision Support (Angel)" },
        
        "ADVANTAGES":{"keywords":["advantanges", "plus points", "pros", "merits", "noted points"],
                      
                      "answer":
            
                        "FTMS FleetPro – Advantages:\n"
                        "✅ Reduces fleet downtime."
                        "✅ Improves operational efficiency."
                        "✅ Lowers maintenance costs."
                        "✅ Prevents missed renewals."
                        "✅ Enhances vehicle safety."
                        "✅ Faster decision-making."
                        "✅ Increases productivity."
                        "✅ Centralized fleet management."
                        "✅ Real-time monitoring."},
        
        "SPECIALITIES":{"keywords":["specialities","special features", "highlights","special tools"],
                        
                        "answer":
            
                        "FTMS FleetPro – Specialities.\n"
                        "⭐ AI-powered insights & Assistant (Angel)"
                        "⭐ Smart Decision Support."
                        "⭐ Predictive Alerts & Reminders."
                        "⭐ Real-time Fleet Monitoring."
                        "⭐ Intelligent Dashboard."
                        "⭐ One-Click PDF Reports."
                        "⭐ User-Friendly Interface."
                        "⭐ Modular & Scalable Design"
                        "⭐ Centralized Fleet Database."
                        "⭐ Detect → Analyze → Suggest Workflow."},
        
        "MODULES":{"keywords":["modules", "program", "programs", "program files"],
                   
                   "answer":
            
                    "FTMS FleetPro – Modules:\n"
                    "🚚 Vehicle Management."
                    "👨‍✈️ Driver Management."
                    "📍 Route Management."
                    "📅 Daily Vehicle Monitoring."
                    "⛽ Fuel Management."
                    "🛠️ Maintenance Management."
                    "🔋 Battery Management."
                    "🛞 Tyre Management."
                    "🚨 Breakdown Management."
                    "🚗 Accident Management."
                    "📄 Insurance & Registration."
                    "📋 Service Scheduling."
                    "💰 Expense Management."
                    "📊 Dashboard & Reports."
                    "⚙️ System Administration."
                    "🤖 AI Assistant (Angel)."},
        
        "COMPETITORS":{"keywords":["competitor", "competitors", "competition","rivals","alternative", 
                                   "alternatives", "other software", "similar softwares", "similar applications",
                                   "compare","who are the compeitors", "market leaders"],
                       "answer":
            
            "Yes.FTMS FleetPro competes with leading Fleet Management & ERP solutions such as.."
                        "Major Competitors."
                        "🚛 Samsara."
                        "🚛 Geotab."
                        "🚛 Verizon Connect."
                        "🚛 Fleetio."
                        "🚛 Motive (KeepTruckin)"
                        "🚛 Azuga"
                        "🚛 GPSWOX"
                        "🚛 Odoo Fleet."},
        
        "FAQ":{"FTMS FleetPro – Frequently Asked Questions (FAQ)"

            """Q1. What is FTMS FleetPro?
            A. An intelligent Fleet Transportation Management System for managing fleet operations.

            Q2. Who can use FTMS FleetPro?
            A. Logistics, distribution, transport, and delivery companies.

            Q3. Does it provide maintenance reminders?
            A. Yes, with automatic alerts for service and expiries.

            Q4. Can it track fuel and maintenance costs?
            A. Yes, with detailed records and reports.

            Q5. Does it generate reports?
            A. Yes, PDF and Excel reports are available.

            Q6. Is it easy to use?
            A. Yes, it has a simple and user-friendly interface.

            Q7. Does it support AI?
            A. Yes, the built-in Angel AI Assistant provides intelligent insights and decision support.

            Q8. Can it reduce fleet operating costs?
            A. Yes, by improving planning, maintenance, and operational efficiency.

            Q9. Is FTMS FleetPro customizable?
            A. Yes, it can be customized to suit different business requirements.

            Q10. What makes FTMS FleetPro unique?
            A. Its AI-powered decision support, operational readiness focus, and intelligent dashboard."""}
            
}

class FTMSKnowledge:
    
    def __init__(self):
        pass
    
    def answer(self, question):
        intent = self.detect_intent(question)
        if intent:
            return FTMS_KNOWLEDGE[intent]["answer"]
        return None
        
    def detect_intent(self, question):
        question = question.lower().strip()
        matches = []
        for intent, info in FTMS_KNOWLEDGE.items():
            if "keywords" not in info:
                continue
            for keyword in info["keywords"]:
                if keyword.lower() in question:
                    matches.append((len(keyword), intent))
        # Prefer the most specific phrase.  This prevents the generic ``ftms``
        # application keyword from hiding requests such as "FTMS features".
        return max(matches, default=(0, None))[1]