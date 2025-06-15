from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from flaskapp.database.models import Organization
from flaskapp.database.models import db

class OrganizationForm(FlaskForm):
    name = StringField('Nombre', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    description = TextAreaField('Descripción', validators=[
        Length(max=500)
    ])
    submit = SubmitField('Guardar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization_id = kwargs.get('obj', None) and kwargs['obj'].id

    def validate_name(self, field):
        query = Organization.query.filter(
            db.func.lower(Organization.name) == db.func.lower(field.data)
        )
        
        # Excluir la organización actual en modo edición
        if self.organization_id:
            query = query.filter(Organization.id != self.organization_id)
        
        if query.first():
            raise ValidationError('Este nombre de organización ya existe')