from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Journal(db.Model):
    __tablename__ = 'diaries'
    jid = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    jtitle = db.Column(db.String, nullable=False)
    jcontent = db.Column(db.String, nullable=False)
    jdate = db.Column(db.Date, nullable=False)
    jcycle = db.Column(db.String, nullable=False)
    jfeeling = db.Column(db.String, nullable=False)
    photo_url = db.Column(db.Text, nullable=False)  # 照片 URL

    def serialize(self):
        return {
            'jid': self.jid,
            'user_id': self.user_id,
            'title': self.jtitle,
            'content': self.jcontent,
            'date': str(self.jdate),
            'cycle': self.jcycle,
            'feeling': self.jfeeling,
            'photo_url': self.photo_url
        }


