from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, DateField, SelectField, ValidationError
from wtforms.validators import DataRequired, Optional
from datetime import date

from flaskapp.database.models import EventStatus

class EventForm(FlaskForm):
    name = StringField('Nombre del Evento', validators=[DataRequired()])
    description = TextAreaField('Descripción', validators=[Optional()])
    start_date = DateField('Fecha de Inicio', default=date.today, validators=[DataRequired()])
    end_date = DateField('Fecha de Término', default=date.today, validators=[DataRequired()])
    status_id = SelectField('Estado', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Guardar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_status_choices()

    def _set_status_choices(self):
        """Cargar estados de evento disponibles (igual que en tu otro módulo)"""
        statuses = EventStatus.query.order_by(EventStatus.id).all()
        self.status_id.choices = [(s.id, s.description) for s in statuses]  # Usamos id como valor y description como etiqueta

    def validate_end_date(self, field):
        if field.data < self.start_date.data:
            raise ValidationError('La fecha de término no puede ser anterior a la de inicio')