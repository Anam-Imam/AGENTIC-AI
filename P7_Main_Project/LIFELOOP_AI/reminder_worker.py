from reminder_agent import check_deadlines

if __name__ == "__main__":
    reminders = check_deadlines()
    print(f"LIFELOOP deadline check complete. Emails sent: {len(reminders)}")
