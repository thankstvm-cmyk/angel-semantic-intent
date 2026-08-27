""" This Engine will handle all types of Date and Time questions
strengthen Angel's ability to reply any questions regarding date, day, month, year, leap year
yesterday, tomorrow, next week, next month, next year. previous day, yesterday, previous week, previous year etc
and all time related questions."""

DATE_KEYWORDS = ["today", "today's date","current date", "date today", "what date", "what date today", "date of today"]

TIME_KEYWORDS = ["current time", "time now", "what time", "what is time now"]


from datetime import datetime, date, timedelta
class DateTimeEngine:
    
    def can_answer(self, question):
        question = question.lower().strip()
        keywords = DATE_KEYWORDS + TIME_KEYWORDS + ["tomorrow", "yesterday", "what month", "what year"]
        return any (word in question for word in keywords)
        
    def answer(self, question):
        question = question.lower().strip()
        if any (k in question for k in DATE_KEYWORDS):
            return self.get_current_date()
        elif any (k in question for k in TIME_KEYWORDS):
            return self.get_current_time()
        elif any(word in question for word in("tomorrow","tommorrow", "tommorow", "tomarrow")):
            return self.get_tomorrow()
        elif any(word in question for word in ("yesterday", "yestarday", "yesturday", "yestaday")):
            return self.get_yesterday()
        elif "month" in question:
            return self.get_month()
        elif "year" in question:
            return self.get_year()
        else:
            return "I understand your question, but I need more specific data or context."
    
    def get_current_date(self):
        now = self.now()
        today = (f"Today's Date is: {now.strftime('%A')}, {now.strftime('%d %B %Y')}.")
        return today
    
    def get_current_time(self): 
        now = self.now()
        timenow = (f"Time now is: {now.strftime('%I:%M:%S %p')}")
        return timenow

    def get_day(self):
        now = self.now()
        today = (f"Today is :{now.strftime('%A')}")
        return today
    
    
    def get_month(self):
        now = self.now()
        month = (f"This month is : {now.strftime('%B')} - ({now.strftime('%m')})")
        return month
    
    def get_tomorrow(self):
        now = self.now() + timedelta(days=1)
        tom = (f"Tommorrow is: {now.strftime('%A')}, {now.strftime('%d %B %Y')}.")
        return tom

    def get_yesterday(self):
        now = self.now() - timedelta(days=1)
        yesday = (f"Yesterday is: {now.strftime('%A')}, {now.strftime('%d %B %Y')}.")
        return yesday
    
    def get_week_number(self):
        now = self.now()
        return f"This is week number {now.strftime('%W')} of the year."
    
    def get_year(self):
        now = self.now()
        year = (f"This year is: {now.strftime('%Y')}")
        return year
    
    def now(self):
        return datetime.now()
    

