from supabase import create_client, Client


# Production Supabase credentials
SUPABASE_URL = "https://vucjpafacklschmseooy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ1Y2pwYWZhY2tsc2NobXNlb295Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0Mjg3MTIsImV4cCI6MjA3NjAwNDcxMn0.T6DL3JsCVMNbgZ1V5Ckj5JUiq1tsapyH3thEgiCQ80o"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_session(user_id, stress_score, emotion, transcribed_text=None):
	"""
	Insert a session record into the 'sessions' table in Supabase.
	"""
	from datetime import datetime
	data = {
		"user_id": user_id,
		"stress_score": stress_score,
		"emotion": emotion,
		"transcribed_text": transcribed_text,
		"timestamp": datetime.utcnow().isoformat()
	}
	return supabase.table("sessions").insert(data).execute()
