from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'User'
    __table_args__ = {'schema': 'DocumentManagementSystem'}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('DocumentManagementSystem.Organization.id'), nullable=False)
    account_type_id = db.Column(db.Integer, db.ForeignKey('DocumentManagementSystem.AccountType.id'), nullable=True, default = 1 )
    registration_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    organization = db.relationship('Organization', backref=db.backref('users', lazy=True))
    account = db.relationship('AccountType', backref=db.backref('users', lazy=True))


class Document(db.Model):
    __tablename__ = 'Document'
    __table_args__ = {'schema': 'DocumentManagementSystem'}

    id = db.Column(db.Integer, primary_key=True)
    user_defined_name = db.Column(db.String(120), nullable=False)
    auto_created_name = db.Column(db.String(120), nullable=False)
    orignal_name = db.Column(db.String(250), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('DocumentManagementSystem.DocumentStatus.id'), default=1)
    user_id = db.Column(db.Integer, db.ForeignKey('DocumentManagementSystem.User.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('documents', lazy=True))
    archived = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    status = db.relationship('DocumentStatus', backref=db.backref('Document', lazy=True))


class AccountType(db.Model):
    __tablename__ = 'AccountType'
    __table_args__ = {'schema': 'DocumentManagementSystem'}

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(120), unique=True, nullable=False)



class Organization(db.Model):
    __tablename__ = 'Organization'
    __table_args__ = {'schema': 'DocumentManagementSystem'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)



class Assignment(db.Model):
    __tablename__ = 'Assignment'
    __table_args__ = {'schema': 'DocumentManagementSystem'}

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('DocumentManagementSystem.Document.id'), nullable=False)
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey('DocumentManagementSystem.User.id'), nullable=False)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('DocumentManagementSystem.User.id'), nullable=False)
    assigned_comment = db.Column(db.Text, nullable=True, default=None)
    reviewer_comment = db.Column(db.Text, nullable=True, default=None)
    assignment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False, default=None)
    status_id = db.Column(db.Integer, db.ForeignKey('DocumentManagementSystem.DocumentStatus.id'), default=1)
    assigned_by_user = db.relationship('User', foreign_keys=[assigned_by_user_id])
    assigned_to_user = db.relationship('User', foreign_keys=[assigned_to_user_id])

class Archive(db.Model):
    __tablename__ = 'Archive'
    __table_args__ = {'schema': 'DocumentManagementSystem'}

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('DocumentManagementSystem.Document.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('DocumentManagementSystem.User.id'), nullable=False)
    archived_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    users = db.relationship('User', backref=db.backref('archives', lazy=True))
    document = db.relationship('Document', backref=db.backref('archives', lazy=True))



class DocumentStatus(db.Model):
    __tablename__ = 'DocumentStatus'
    __table_args__ = {'schema': 'DocumentManagementSystem'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
