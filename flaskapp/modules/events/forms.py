from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DateField, SelectField, ValidationError
from wtforms.validators import DataRequired, Optional
from datetime import date

class EventForm(FlaskForm):
    name = StringField('Nombre del Evento', validators=[DataRequired()])
    description = TextAreaField('Descripción', validators=[Optional()])
    start_date = DateField('Fecha de Inicio', default=date.today, validators=[DataRequired()])
    end_date = DateField('Fecha de Término', default=date.today, validators=[DataRequired()])
    status = SelectField('Estado', coerce=str, validators=[DataRequired()])
    submit = SubmitField('Guardar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from flaskapp.database.models import EventStatus
        self.status.choices = [
            (status.code, status.description) 
            for status in EventStatus.query.order_by(EventStatus.id).all()
        ]

    def validate_end_date(self, field):
        if field.data < self.start_date.data:
            raise ValidationError('La fecha de término no puede ser anterior a la de inicio')