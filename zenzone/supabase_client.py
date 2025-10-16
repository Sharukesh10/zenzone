from supabase import create_client, Client
import os


# Production Supabase credentials
SUPABASE_URL = os.environ.get('SUPABASE_URL', "https://vucjpafacklschmseooy.supabase.co")
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ1Y2pwYWZhY2tsc2NobXNlb295Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0Mjg3MTIsImV4cCI6MjA3NjAwNDcxMn0.T6DL3JsCVMNbgZ1V5Ckj5JUiq1tsapyH3thEgiCQ80o")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', "your-service-role-key-here")  # Replace with actual service role key

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

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

def create_user(email, password, name, age, college):
	"""
	Create a new user in Supabase Auth and insert user profile.
	"""
	try:
		# Create auth user
		auth_response = supabase.auth.sign_up({
			"email": email,
			"password": password
		})

		if auth_response.user:
			user_id = auth_response.user.id

			# Insert user profile using admin client
			profile_data = {
				"id": user_id,
				"email": email,
				"name": name,
				"age": int(age),
				"college": college
			}
			supabase_admin.table("users").insert(profile_data).execute()

			return {"success": True, "user": auth_response.user}
		else:
			return {"success": False, "error": "Failed to create user"}
	except Exception as e:
		return {"success": False, "error": str(e)}

def login_user(email, password):
	"""
	Log in user with Supabase Auth.
	"""
	try:
		auth_response = supabase.auth.sign_in_with_password({
			"email": email,
			"password": password
		})
		return {"success": True, "user": auth_response.user, "session": auth_response.session}
	except Exception as e:
		return {"success": False, "error": str(e)}

def get_current_user():
	"""
	Get current authenticated user.
	"""
	try:
		user = supabase.auth.get_user()
		return user.user if user else None
	except Exception as e:
		return None

def logout_user():
	"""
	Log out current user.
	"""
	try:
		supabase.auth.sign_out()
		return {"success": True}
	except Exception as e:
		return {"success": False, "error": str(e)}
