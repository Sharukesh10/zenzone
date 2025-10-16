from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    sessions = db.relationship('Session', backref='user', lazy=True)

class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    stress_score = db.Column(db.Float, nullable=False)
    emotion = db.Column(db.String(50), nullable=False)
    text_content = db.Column(db.Text)
    audio_features = db.Column(db.JSON)
    suggested_activity = db.Column(db.String(100))

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'stress_score': self.stress_score,
            'emotion': self.emotion,
            'text_content': self.text_content,
            'suggested_activity': self.suggested_activity
        }