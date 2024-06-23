from flask import Blueprint, Flask, redirect, url_for, request, render_template, render_template_string
from flask_login import login_required, current_user
from sqlalchemy import func
from .models import db
import uuid
from .aws_utils import FileManagementUtils
import os

views = Blueprint('views', __name__)
aws_util = FileManagementUtils(bucket_name = os.environ.get('bucket_name'), region_name=os.environ.get('region_name'), aws_access_key_id = os.environ.get('aws_access_key_id') , aws_secret_access_key = os.environ.get('aws_secret_access_key') )

@views.route('/')
@login_required
def home():
    from .models import User

    cur_user = User.query.filter(User.id == current_user.id).first()

    return render_template('index.html', user_data = cur_user)



@views.route('/view_document/<int:document_id>')
@login_required
def view_document(document_id):
    from .aws_utils import FileManagementUtils
    from .models import Document

    doc_name =  Document.query.filter( Document.is_deleted == False ).first()

    url = aws_util.create_presigned_url(doc_name.auto_created_name, type = 'view' )

    return redirect(url)

    # return redirect(url_for("views.dashboard"))





@views.route('/download/<int:document_id>')
@login_required
def download_document(document_id):
    from .models import Document

    doc_name =  Document.query.filter_by(id = document_id).first()
    

    url = aws_util.create_presigned_url(doc_name.auto_created_name, type = 'download' )

    return redirect(url)


@views.route('/assign/<int:document_id>', methods=["GET", "POST"])
@login_required
def assign_document(document_id):
    from .models import Document , DocumentStatus,  Assignment, User

    if request.method == "GET":

        users = User.query.filter(User.organization_id == current_user.organization_id, User.id != current_user.id).with_entities(User.id, (User.first_name + ' ' + User.last_name).label('name')).all()
        documents = Document.query.join(DocumentStatus, Document.status_id==DocumentStatus.id).add_columns(Document.user_defined_name, Document.upload_date,  DocumentStatus.name  ).filter(Document.archived == False, Document.is_deleted == False, Document.id == document_id ).first()

        
        # users = User.query.filter_by(organization_id=current_user.organization_id).with_entities(User.id, (User.first_name + ' ' + User.last_name).label('name')).all()
        return render_template("assign_document_extended.html", users = users, document = documents)

    elif request.method == "POST":
        assigned_to_user_id = request.form.get('option')
        assigned_comment = request.form.get('comment')
        due_date = request.form.get('due_date')

        assigned_document = Document.query.filter(Document.archived == False, Document.is_deleted == False, Document.id == document_id ).first()
        
        new_assignment = Assignment(document_id = document_id, assigned_by_user_id = current_user.id, assigned_to_user_id = assigned_to_user_id, assigned_comment = assigned_comment, due_date = due_date, status_id = 2)

        assigned_document.status_id = 2

        db.session.add(new_assignment)

        db.session.commit()
        
        return redirect(url_for("views.assignment"))



@views.route('/review', methods = ['GET'])
@login_required
def all_reviews():
    return render_template('all_review.html')



@views.route('/review/assignation', methods = ['GET'])
@login_required
def assignation_details():
    from .models import Document , DocumentStatus,  Assignment, User

    documents = Assignment.query.join(Document, Document.id == Assignment.document_id)\
        .join(DocumentStatus, Assignment.status_id==DocumentStatus.id)\
        .join(User, Assignment.assigned_to_user_id == User.id)\
        .add_columns(Assignment.id.label('assigment_id'), Document.id, Document.user_defined_name,  DocumentStatus.name,  func.date_trunc('second', Assignment.assignment_date).label('assignment_date'),   func.concat(User.first_name, '  ', User.last_name).label('assigned_user_name') )\
        .filter(Document.archived == False, Assignment.assigned_by_user_id == current_user.id, Document.is_deleted == False ).all()

    
    return render_template('assignation_details.html', documents = zip([id for id in range(1, len(documents) + 1) ], documents))




@views.route('/review/assignation/edit/<int:assignment_id>', methods = ['GET', 'POST'])
@login_required
def assignation_details_details(assignment_id):
    from .models import Document , DocumentStatus,  Assignment, User

    if request.method == 'GET':

        users = User.query.filter(User.organization_id == current_user.organization_id, User.id != current_user.id).with_entities(User.id, (User.first_name + ' ' + User.last_name).label('name')).all()

        assigned_documents_detail = Assignment.query\
            .join(Document,  Document.id == Assignment.document_id)\
            .join(DocumentStatus, Document.status_id==DocumentStatus.id)\
            .add_columns(Document.id, Document.user_defined_name, DocumentStatus.name, Document.upload_date, Assignment.due_date, Assignment.assigned_comment, Assignment.reviewer_comment)\
            .filter(Document.archived == False, Assignment.id == assignment_id, Document.is_deleted == False ).first()
        

        default_due_date  = assigned_documents_detail.due_date.strftime("%Y-%m-%d")



        return render_template('assigned_document_edit.html', document = assigned_documents_detail, users = users, due_date = default_due_date)


    elif request.method == "POST":
        assignment_document = Assignment.query.filter(Assignment.id == assignment_id ).first()

        assignment_document.assigned_to_user_id = request.form.get('option')
        assignment_document.assigned_comment = request.form.get('comment')
        assignment_document.due_date = request.form.get('due_date')

        db.session.commit()

        return redirect(url_for("views.assignation_details"))






@views.route('/review/assigned_to_user', methods = ['GET'])
@login_required
def assignation_to_me():
    from .models import Document , DocumentStatus,  Assignment, User

    documents = Assignment.query.join(Document, Document.id == Assignment.document_id)\
        .join(DocumentStatus, Assignment.status_id==DocumentStatus.id)\
        .join(User, Assignment.assigned_by_user_id == User.id)\
        .add_columns(Assignment.id.label('assignment_id'), Document.id, Document.user_defined_name,  DocumentStatus.name, func.date( Assignment.due_date).label('due_date'), func.concat(User.first_name, '  ', User.last_name).label('assigned_user_name') )\
        .filter(Document.archived == False, Assignment.assigned_to_user_id == current_user.id, Document.is_deleted == False , Assignment.status_id not in (3,4) ).all()

    

    
    return render_template('review.html', documents = zip([id for id in range(1, len(documents) + 1) ], documents))






@views.route('/review/assigned_to_user/respond//<int:assignment_id>', methods = ['GET', 'POST'])
@login_required
def assignation_to_me_respond(assignment_id):
    from .models import Document , DocumentStatus,  Assignment, User

    if request.method == 'GET':


        assigned_documents_detail = Assignment.query\
            .join(Document,  Document.id == Assignment.document_id)\
            .join(DocumentStatus, Document.status_id==DocumentStatus.id)\
            .add_columns(Document.id, Document.user_defined_name, DocumentStatus.name, Document.upload_date, Assignment.due_date, Assignment.assigned_comment)\
            .filter(Document.archived == False, Assignment.id == assignment_id, Document.is_deleted == False ).first()
        

        default_due_date  = assigned_documents_detail.due_date.strftime("%Y-%m-%d")



        return render_template('review_extended.html', document = assigned_documents_detail,  due_date = default_due_date)


    elif request.method == "POST":

        
        assignment_document = Assignment.query.filter(Assignment.id == assignment_id ).first()

        document = Document.query.join(Assignment, Assignment.document_id == Document.id).filter(Assignment.id == assignment_id).first()
        
        status_code = 3 if 'accept' in request.form else 4

        document.status_id = status_code


        assignment_document.status_id = status_code

        assignment_document.reviewer_comment = request.form.get('review_comment')

        db.session.commit()


        return redirect(url_for("views.assignation_to_me"))





@views.route('/assign', methods=["GET"])
@login_required
def assignment():
    from .models import Document , DocumentStatus,  Assignment, User

    documents = Document.query\
        .join(DocumentStatus, Document.status_id==DocumentStatus.id)\
        .join(User, Document.user_id == User.id)\
        .add_columns(Document.id, Document.user_defined_name,   DocumentStatus.name )\
        .filter(Document.archived == False, Document.user_id == current_user.id, Document.is_deleted == False ).all()


    print(documents)

    return render_template("assigndocument.html", documents = zip([id for id in range(1, len(documents) + 1) ], documents))



@views.route('/delete/<int:document_id>')
@login_required
def delete_document(document_id):
    from .models import Document,Archive

    try:
        doc_name =  Document.query.filter_by(id = document_id).first()

        doc_name.is_deleted = True
        
        archived_doc_name =  Archive.query.filter_by(document_id = document_id).first()

        aws_util.delete_obj(doc_name.auto_created_name )

        db.session.delete(archived_doc_name)
        db.session.commit()

    except Exception as e:
        print(e)

    return redirect(url_for("views.archived_documents"))




@views.route('/archive_document/<int:document_id>/<int:archive_type>', methods=["GET", "POST"])
@login_required
def update_document_archive(document_id, archive_type):
    from .models import Document, Archive

    

    doc =  Document.query.filter_by(id = document_id).filter(Document.is_deleted == False ).first()

    if doc:
        print(document_id, archive_type)
        try:
            if archive_type == 1:
                archived_documents = Archive(document_id=document_id, user_id = current_user.id)
                db.session.add(archived_documents)
                doc.archived = bool(archive_type)
                db.session.commit()



            elif  archive_type == 0:
                archive_ = Archive.query.filter_by(document_id = document_id).first()
                doc.archived = bool(archive_type)
                db.session.delete(archive_)
                db.session.commit()

        except Exception as e:
            print(e)
    
    return redirect(url_for("views.archived_documents"))








@views.route('/add_document', methods=["GET", "POST"])
@login_required
def add_document():
    from .aws_utils import FileManagementUtils
    from .models import Document

    if request.method == "POST":
        uploaded_file = request.files["file"]
        user_defined_file = request.form.get('filename')

        file_extension = uploaded_file.filename.rsplit('.', 1)[1].lower()  if '.' in uploaded_file.filename  else '.'
        
        if FileManagementUtils.allowed_file(uploaded_file.filename):

            new_filename = uuid.uuid4().hex + '.' + uploaded_file.filename.rsplit('.', 1)[1].lower()


            new_filename = uuid.uuid4().hex + '.' + uploaded_file.filename.rsplit('.', 1)[1].lower()
            aws_util.upload_file(uploaded_file, new_filename, file_extension)
            

            file = Document(user_defined_name = user_defined_file, auto_created_name =  new_filename , orignal_name = uploaded_file.filename, user_id = current_user.id)
            db.session.add(file)
            db.session.commit()
        

        return redirect(url_for("views.dashboard"))

    return render_template('add_document.html')


@views.route('/dashboard', methods=["GET", "POST"])
@login_required
def dashboard():
    from .models import Document, DocumentStatus

    
    documents = Document.query.join(DocumentStatus, Document.status_id==DocumentStatus.id).add_columns(Document.id, Document.user_defined_name, Document.user_id,func.date_trunc('second', Document.upload_date).label('date'), DocumentStatus.name,   ).filter(Document.archived == False, Document.user_id == current_user.id, Document.is_deleted == False ).all()

    # documents = db.session.query(Document, DocumentStatus.name).outerjoin(DocumentStatus, DocumentStatus.id == Document.status_id).filter(Document.archived == False, Document.user_id == current_user.id ).all()
    

    return render_template('dashboard.html', documents = zip([id for id in range(1, len(documents) + 1) ], documents) )




@views.route('/archived_documents', methods=["GET"])
@login_required
def archived_documents():
    from .models import Archive, Document
    
    documents = Archive.query.join(Document, Document.id==Archive.document_id).add_columns( Archive.document_id, Document.user_defined_name, Archive.user_id, func.date_trunc('second', Document.upload_date).label('Created_Date'), func.date_trunc('second', Archive.archived_date).label('Archived_Date') ).filter(Document.archived == True, Document.user_id == current_user.id ).all()    

    return render_template('archived_documents.html', documents = zip([id for id in range(1, len(documents) + 1) ], documents) )







